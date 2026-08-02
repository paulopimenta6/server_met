"""Captação contínua: verifica novos ciclos GFS e METARs automaticamente.

O `SchedulerRunner` roda em segundo plano dentro do servidor (lifespan):
- a cada `scheduler_grib_interval_min` (padrão 60 min) verifica se o ciclo
  GFS mais recente já foi publicado no NOMADS e, se sim, baixa os arquivos
  e executa o pipeline automático (mapas, matrizes e análises das regiões
  predefinidas);
- a cada `scheduler_metar_interval_min` (padrão 30 min) busca as observações
  METAR das estações.

O estado fica persistido na tabela `ingest_state` para sobreviver a reinícios.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from server_MET.acquisition.grib_downloader import GribDownloader
from server_MET.acquisition.metar_client import MetarClient
from server_MET.core.config import Settings
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.repositories import IngestStateRepository

logger = get_logger(__name__)

#: Atraso de publicação do NOMADS após o início do ciclo (~4-5 horas).
PUBLISH_DELAY_HOURS = 5

#: (variável, nível) gerados automaticamente pelo pipeline por região.
PIPELINE_VARS: list[tuple[str, Optional[int]]] = [
    ("temp", 500),
    ("temp", 850),
    ("umidadeRel", 850),
    ("winds", None),
    ("chuvaNaoConvec", None),
]


def latest_published_cycle(now: Optional[datetime] = None) -> tuple[str, str]:
    """Data/análise do ciclo GFS mais recente que já deve estar publicado."""
    now = now or datetime.now()
    pub = now - timedelta(hours=PUBLISH_DELAY_HOURS)
    cycle = pub.hour - (pub.hour % 6)
    return pub.strftime("%Y%m%d"), f"{cycle:02d}"


def previous_cycle(date_str: str, analysis: str) -> tuple[str, str]:
    """Ciclo anterior (6 horas antes)."""
    dt = datetime.strptime(f"{date_str} {analysis}", "%Y%m%d %H")
    prev = dt - timedelta(hours=6)
    return prev.strftime("%Y%m%d"), prev.strftime("%H")


class SchedulerRunner:
    """Executor dos loops de captação contínua (GRIB + METAR)."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self.state = IngestStateRepository()
        self.downloader = GribDownloader()
        self.metar = MetarClient()
        self._grib_lock = asyncio.Lock()
        self._grib_task: Optional[asyncio.Task] = None
        self._metar_task: Optional[asyncio.Task] = None
        self._running = False
        self.pipeline_running = False

    # ---------------------------------------------------------- ciclo GRIB
    async def _grib_loop(self) -> None:
        logger.info("Loop GRIB iniciado (intervalo: %d min)",
                    self.settings.scheduler_grib_interval_min)
        while self._running:
            try:
                await self._process_new_cycles()
            except Exception as e:  # nunca derruba o loop
                logger.exception("Erro no ciclo GRIB: %s", e)
            await asyncio.sleep(self.settings.scheduler_grib_interval_min * 60)

    async def _process_new_cycles(self) -> None:
        async with self._grib_lock:
            self.state.set("last_grib_check", _now_iso())
            processed = self.state.get_json("processed_cycles", []) or []
            target = latest_published_cycle()
            candidates = [target, previous_cycle(*target)]

            for date_str, ana in candidates:
                key = f"{date_str}_{ana}"
                if key in processed:
                    continue
                logger.info("Verificando ciclo %s %sZ", date_str, ana)
                files = await asyncio.to_thread(
                    self.downloader.download_gribs_all_resolutions,
                    date_str=date_str,
                    analysis_hour=ana,
                )
                if not files:
                    logger.info("Ciclo %s %sZ ainda não disponível.", date_str, ana)
                    continue
                await asyncio.to_thread(self._run_pipeline, date_str, ana)
                processed = [key] + [p for p in processed if p != key]
                self.state.set_json("processed_cycles", processed[:10])
                self.state.set("last_pipeline_cycle", key)
                return

    def _run_pipeline(self, date_str: str, ana: str) -> None:
        """Gera mapas, matrizes e análises das regiões predefinidas."""
        from server_MET.analysis.profiles import ProfileAnalyzer
        from server_MET.analysis.statistics import StatisticsAnalyzer
        from server_MET.analysis.timeseries import TimeSeriesAnalyzer
        from server_MET.output.maps import MapGenerator
        from server_MET.output.matrices import MatrixGenerator
        from server_MET.persistence.repositories import AnalysisRepository
        from server_MET.processing.regions import (
            CIDADES_PREDEFINIDAS,
            REGIOES_PREDEFINIDAS,
            Region,
        )

        self.pipeline_running = True
        try:
            regions = list(REGIOES_PREDEFINIDAS) + list(CIDADES_PREDEFINIDAS)
            regions = [r for r in regions if r != "SA"]
            if self.settings.scheduler_auto_pipeline:
                allowed = set(self.settings.scheduler_auto_pipeline)
                regions = [r for r in regions if r in allowed]

            map_gen = MapGenerator()
            matrix_gen = MatrixGenerator()
            stats = StatisticsAnalyzer()
            profiles = ProfileAnalyzer()
            series = TimeSeriesAnalyzer()
            analysis_repo = AnalysisRepository()

            total = 0
            for region_name in regions:
                region = Region(name=region_name)
                for var_name, level in PIPELINE_VARS:
                    try:
                        total += len(map_gen.generate(
                            var_name, region, level, date_str, ana,
                        ))
                        matrix_gen.generate(
                            var_name, region, level, date_str, ana,
                        )
                        rows = stats.summarize(var_name, region, level, date_str, ana)
                        if rows:
                            analysis_repo.save(
                                "summary",
                                {"variable": var_name, "region": region.name,
                                 "date": date_str, "analysis": ana,
                                 "results": rows},
                                var_name, level, region.name, date_str, ana,
                            )
                        prof = profiles.profile(var_name, region, date_str, ana)
                        if prof.get("profile"):
                            analysis_repo.save(
                                "profile", prof, var_name, None,
                                region.name, date_str, ana,
                            )
                        ts = series.timeseries(var_name, region, level, date_str, ana)
                        if ts.get("series"):
                            analysis_repo.save(
                                "timeseries", ts, var_name, level,
                                region.name, date_str, ana,
                            )
                    except Exception as e:
                        logger.warning(
                            "Pipeline: falha em %s/%s/%s: %s",
                            region_name, var_name, level, e,
                        )
            logger.info("Pipeline %s %sZ concluído (%d mapas).",
                        date_str, ana, total)
        finally:
            self.pipeline_running = False

    # ------------------------------------------------------------ METAR
    async def _metar_loop(self) -> None:
        logger.info("Loop METAR iniciado (intervalo: %d min)",
                    self.settings.scheduler_metar_interval_min)
        while self._running:
            try:
                await asyncio.to_thread(self._fetch_all_metars)
            except Exception as e:
                logger.exception("Erro no loop METAR: %s", e)
            await asyncio.sleep(self.settings.scheduler_metar_interval_min * 60)

    def _fetch_all_metars(self) -> None:
        self.state.set("last_metar_fetch", _now_iso())
        results = self.metar.get_all_metars()
        self.state.set("last_metar_count", str(len(results)))
        logger.info("METAR atualizado: %d estações.", len(results))

    # --------------------------------------------------- lifecycle / API
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._grib_task = asyncio.create_task(self._grib_loop())
        self._metar_task = asyncio.create_task(self._metar_loop())

    def stop(self) -> None:
        self._running = False
        for task in (self._grib_task, self._metar_task):
            if task:
                task.cancel()
        self._grib_task = self._metar_task = None

    def run_now(self) -> str:
        """Dispara uma verificação imediata de ciclo GFS (sem esperar o loop)."""
        asyncio.create_task(self._process_new_cycles())
        return "verificacao_iniciada"

    def status(self) -> dict:
        return {
            "enabled": self.settings.scheduler_enabled,
            "running": self._running,
            "pipeline_running": self.pipeline_running,
            "grib_interval_min": self.settings.scheduler_grib_interval_min,
            "metar_interval_min": self.settings.scheduler_metar_interval_min,
            "last_grib_check": self.state.get("last_grib_check"),
            "last_metar_fetch": self.state.get("last_metar_fetch"),
            "last_metar_count": self.state.get("last_metar_count"),
            "last_pipeline_cycle": self.state.get("last_pipeline_cycle"),
            "processed_cycles": self.state.get_json("processed_cycles", []),
        }


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


#: Instância única compartilhada entre o lifespan e as rotas da API.
_runner: Optional[SchedulerRunner] = None


def get_scheduler_runner() -> SchedulerRunner:
    global _runner
    if _runner is None:
        _runner = SchedulerRunner()
    return _runner


__all__ = [
    "SchedulerRunner",
    "get_scheduler_runner",
    "latest_published_cycle",
    "previous_cycle",
    "PIPELINE_VARS",
]
