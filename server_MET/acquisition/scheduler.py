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
from server_MET.core.constants import MAIN_VARIABLES, PIPELINE_LEVELS
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.repositories import IngestStateRepository

logger = get_logger(__name__)

#: Atraso de publicação do NOMADS após o início do ciclo (~4-5 horas).
PUBLISH_DELAY_HOURS = 5

#: (variável, nível) gerados automaticamente pelo pipeline por região.
#: Conjunto enxuto: principais variáveis meteorológicas + poluição, com os
#: níveis fixos do sistema (superfície, 850, 500 e 200 hPa — ver
#: `Settings.pipeline_levels` / `PIPELINE_LEVELS`). Variáveis com nível `None`
#: que estão em `PIPELINE_LEVELED_VARS` são expandidas para os níveis fixos;
#: as demais são de superfície/nível próprio. `winds` é calculado (uSupe/vSupe).
PIPELINE_VARS: list[tuple[str, Optional[int]]] = [
    (var_name, None) for var_name in MAIN_VARIABLES
] + [("winds", None)]

#: Variáveis do pipeline cujo nível é variável e deve ser expandido para os
#: níveis fixos do sistema (850, 500 e 200 hPa). `nuvem`/`nuvemTot` são
#: colunas únicas (nível atmosférico) e ficam fora da expansão.
PIPELINE_LEVELED_VARS: tuple[str, ...] = ("temp", "umidadeRel", "ozonio")

#: (variável, nível) das estatísticas geradas automaticamente pelo pipeline,
#: persistidas na tabela `statistics` e em CSV — principais variáveis nos
#: níveis fixos do sistema.
PIPELINE_STATS_VARS: list[tuple[str, Optional[int]]] = [
    ("temp", 850),
    ("temp", 500),
    ("temp", 200),
    ("umidadeRel", 850),
    ("dewpoint2m", None),
    ("temps2m", None),
    ("rh2m", None),
    ("nuvemTot", None),
    ("precipitacao", None),
    ("chuvaNaoConvec", None),
    ("chuvaConvec", None),
    ("winds", None),
    ("ps", None),
    ("ozonio", 850),
    ("ozonio", 500),
    ("ozonioTot", None),
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
        from server_MET.processing.processor import DataProcessor

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
                    resolutions=[self.settings.scheduler_resolution],
                )
                if not files:
                    logger.info("Ciclo %s %sZ ainda não disponível.", date_str, ana)
                    continue

                processor = DataProcessor()
                complete, missing = await asyncio.to_thread(
                    self._cycle_has_complete_forecast, date_str, ana, processor
                )
                if not complete:
                    logger.warning(
                        "Ciclo %s %sZ incompleto (horas faltando/inválidas: %s). "
                        "Não será marcado como processado; re-verificando depois.",
                        date_str, ana, ", ".join(missing),
                    )
                    continue

                await asyncio.to_thread(self._run_pipeline, date_str, ana, processor)
                processed = [key] + [p for p in processed if p != key]
                self.state.set_json("processed_cycles", processed[:10])
                self.state.set("last_pipeline_cycle", key)
                return

    def _cycle_has_complete_forecast(
        self, date_str: str, ana: str, processor=None
    ) -> tuple[bool, list[str]]:
        """Verifica se todas as horas de `Settings.forecast_hours` do ciclo
        existem no disco e estão saudáveis (resolução primária do scheduler).

        A validação usa o `GribReader` compartilhado do `DataProcessor`, então
        o resultado fica em cache e o pipeline não re-valida os mesmos GRIBs.
        """
        from server_MET.processing.processor import DataProcessor

        processor = processor or DataProcessor()
        resolution = self.settings.scheduler_resolution
        missing = []
        for fh in self.settings.forecast_hours:
            f = processor.reader.find_grib_file(date_str, ana, fh, resolution)
            if (
                f is None
                or not f.exists()
                or f.stat().st_size == 0
                or not processor.reader.is_healthy(f)
            ):
                missing.append(fh)
        return not missing, missing

    def _run_pipeline(self, date_str: str, ana: str, processor=None) -> None:
        """Gera mapas e matrizes CSV das regiões predefinidas (por nível).

        Análises (summary/timeseries) ficam sob demanda; profile é gerado
        para cada variável com nível (percorre os níveis internamente).
        """
        from server_MET.analysis.profiles import ProfileAnalyzer
        from server_MET.output.maps import MapGenerator
        from server_MET.output.matrices import MatrixGenerator
        from server_MET.persistence.repositories import AnalysisRepository
        from server_MET.processing.processor import DataProcessor
        from server_MET.processing.regions import Region, todas_as_regioes

        self.pipeline_running = True
        try:
            regions = list(todas_as_regioes())
            regions = [r for r in regions if r != "SA"]
            if self.settings.scheduler_auto_pipeline:
                allowed = set(self.settings.scheduler_auto_pipeline)
                regions = [r for r in regions if r in allowed]

            combos = self._expand_pipeline_combos(date_str, ana)

            # Processador (e GribReader) compartilhado: validação dos GRIBs
            # ocorre 1x por ciclo (cache em `GribReader._healthy_cache`).
            processor = processor or DataProcessor()
            map_gen = MapGenerator(processor=processor)
            matrix_gen = MatrixGenerator(processor=processor)
            profiles = ProfileAnalyzer(processor=processor)
            analysis_repo = AnalysisRepository()

            total = 0
            for region_name in regions:
                region = Region(name=region_name)
                for var_name, level in combos:
                    try:
                        total += len(map_gen.generate(
                            var_name, region, level, date_str, ana,
                        ))
                        matrix_gen.generate(
                            var_name, region, level, date_str, ana,
                        )
                        if var_name in PIPELINE_LEVELED_VARS and level is None:
                            prof = profiles.profile(var_name, region, date_str, ana)
                            if prof.get("profile"):
                                analysis_repo.save(
                                    "profile", prof, var_name, None,
                                    region.name, date_str, ana,
                                )
                    except Exception as e:
                        logger.warning(
                            "Pipeline: falha em %s/%s/%s: %s",
                            region_name, var_name, level, e,
                        )

            if self.settings.scheduler_auto_statistics:
                try:
                    self._run_statistics(regions, date_str, ana, processor)
                except Exception as e:
                    logger.warning("Pipeline: falha nas estatísticas: %s", e)

            logger.info("Pipeline %s %sZ concluído (%d mapas).",
                        date_str, ana, total)
        finally:
            self.pipeline_running = False

    def _run_statistics(
        self,
        regions: list[str],
        date_str: str,
        ana: str,
        processor=None,
    ) -> None:
        """Gera estatísticas (tabela `statistics` + CSV) das variáveis do
        pipeline para as regiões — dashboard fica sob demanda via API."""
        from server_MET.analysis.statistics import StatisticsAnalyzer
        from server_MET.output.statistics import StatisticsCSVGenerator
        from server_MET.persistence.repositories import StatisticsRepository
        from server_MET.processing.processor import DataProcessor
        from server_MET.processing.regions import Region

        processor = processor or DataProcessor()
        stats = StatisticsAnalyzer(processor=processor)
        stats_repo = StatisticsRepository()
        csv_gen = StatisticsCSVGenerator()

        for region_name in regions:
            region = Region(name=region_name)
            for var_name, level in PIPELINE_STATS_VARS:
                try:
                    summary = stats.summarize(var_name, region, level, date_str, ana)
                    if not summary:
                        continue
                    resolved_level = summary[0].get("level")
                    rows = [
                        dict(r, date_str=date_str, analysis=ana)
                        for r in summary
                    ]
                    stats_repo.delete(var_name, region.name, date_str, ana, resolved_level)
                    stats_repo.save_many(rows)
                    csv_gen.generate(
                        rows, region, var_name, resolved_level, date_str, ana,
                    )
                except Exception as e:
                    logger.warning(
                        "Pipeline: estatísticas de %s/%s/%s falharam: %s",
                        region_name, var_name, level, e,
                    )

    def _expand_pipeline_combos(
        self, date_str: str, ana: str
    ) -> list[tuple[str, Optional[int]]]:
        """Expande `PIPELINE_VARS`: níveis `None` de variáveis com nível viram
        os níveis fixos do sistema (`Settings.pipeline_levels`)."""
        levels = self.settings.pipeline_levels or list(PIPELINE_LEVELS)

        combos: list[tuple[str, Optional[int]]] = []
        for var_name, level in PIPELINE_VARS:
            if level is None and var_name in PIPELINE_LEVELED_VARS:
                combos.extend((var_name, lvl) for lvl in levels)
            else:
                combos.append((var_name, level))
        return combos

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
    "PIPELINE_LEVELED_VARS",
    "PIPELINE_STATS_VARS",
]
