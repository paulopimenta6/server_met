"""Configuração central (singleton) do servidor meteorológico.

Lê `environment/path.conf` (formato `chave=valor`, sem seções) e resolve os
caminhos relativos à raiz do projeto. NUNCA hardcode `data/...` no código —
use sempre `Settings`.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from server_MET.core.constants import FORECAST_HOURS, GFS_BASE_URL


class Settings:
    _instance: Optional["Settings"] = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
        self.ENV_FILE = self.PROJECT_ROOT / "environment" / "path.conf"
        self._dir_gribs: Optional[str] = None
        self._dir_mapas: Optional[str] = None
        self._dir_matrizes: Optional[str] = None
        self._dir_matrizes_predi: Optional[str] = None
        self._dir_matrizes_bluesky: Optional[str] = None
        self._dir_analise: Optional[str] = None
        self._dir_tmp: Optional[str] = None
        self._db_file: Optional[str] = None
        self._scheduler_enabled: Optional[str] = None
        self._scheduler_grib_interval_min: Optional[str] = None
        self._scheduler_metar_interval_min: Optional[str] = None
        self._scheduler_auto_pipeline: Optional[str] = None
        self._scheduler_auto_statistics: Optional[str] = None
        self._forecast_hours: Optional[str] = None
        self._pipeline_levels: Optional[str] = None
        self._parse_env_file()

    def _parse_env_file(self) -> None:
        if not self.ENV_FILE.exists():
            return
        with open(self.ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "dir_gribs":
                    self._dir_gribs = value
                elif key == "dir_mapas":
                    self._dir_mapas = value
                elif key == "dir_matrizes":
                    self._dir_matrizes = value
                elif key == "dir_matrizes_predi":
                    self._dir_matrizes_predi = value
                elif key == "dir_matrizes_bluesky":
                    self._dir_matrizes_bluesky = value
                elif key == "dir_analise":
                    self._dir_analise = value
                elif key == "dir_tmp":
                    self._dir_tmp = value
                elif key == "db_file":
                    self._db_file = value
                elif key == "scheduler_enabled":
                    self._scheduler_enabled = value
                elif key == "scheduler_grib_interval_min":
                    self._scheduler_grib_interval_min = value
                elif key == "scheduler_metar_interval_min":
                    self._scheduler_metar_interval_min = value
                elif key == "scheduler_auto_pipeline":
                    self._scheduler_auto_pipeline = value
                elif key == "scheduler_auto_statistics":
                    self._scheduler_auto_statistics = value
                elif key == "forecast_hours":
                    self._forecast_hours = value
                elif key == "pipeline_levels":
                    self._pipeline_levels = value

    def _resolve_dir(self, path_str: Optional[str], default_subdir: str) -> Path:
        if path_str:
            p = Path(path_str)
            return p if p.is_absolute() else self.PROJECT_ROOT / p
        return self.PROJECT_ROOT / default_subdir

    @property
    def dir_gribs(self) -> Path:
        return self._resolve_dir(self._dir_gribs, "data/gribs")

    @property
    def dir_mapas(self) -> Path:
        return self._resolve_dir(self._dir_mapas, "data/mapasGrib")

    @property
    def dir_matrizes(self) -> Path:
        return self._resolve_dir(self._dir_matrizes, "data/matrizGrib")

    @property
    def dir_matrizes_predi(self) -> Path:
        return self._resolve_dir(self._dir_matrizes_predi, "data/matrizGrib/predi")

    @property
    def dir_matrizes_bluesky(self) -> Path:
        return self._resolve_dir(self._dir_matrizes_bluesky, "data/matrizGrib/bluesky")

    @property
    def dir_analise(self) -> Path:
        return self._resolve_dir(self._dir_analise, "data/analise")

    @property
    def dir_tmp(self) -> Path:
        return self._resolve_dir(self._dir_tmp, "data/tmp")

    @property
    def db_path(self) -> Path:
        return self._resolve_dir(self._db_file, "data/met_server.db")

    @property
    def gfs_url(self) -> str:
        return GFS_BASE_URL

    @property
    def scheduler_enabled(self) -> bool:
        """Captação contínua ligada? Padrão: sim."""
        if self._scheduler_enabled is None:
            return True
        return self._scheduler_enabled.strip().lower() in ("1", "true", "yes", "sim", "on")

    @property
    def scheduler_grib_interval_min(self) -> int:
        """Intervalo (min) entre verificações de novo ciclo GFS. Padrão: 60."""
        try:
            return max(10, int(self._scheduler_grib_interval_min))
        except (TypeError, ValueError):
            return 60

    @property
    def scheduler_metar_interval_min(self) -> int:
        """Intervalo (min) entre buscas de METAR. Padrão: 30."""
        try:
            return max(5, int(self._scheduler_metar_interval_min))
        except (TypeError, ValueError):
            return 30

    @property
    def scheduler_auto_pipeline(self) -> list[str]:
        """Regiões do pipeline automático (vazio = todas predefinidas)."""
        if not self._scheduler_auto_pipeline:
            return []
        return [r.strip().upper() for r in self._scheduler_auto_pipeline.split(",") if r.strip()]

    @property
    def scheduler_auto_statistics(self) -> bool:
        """Pipeline automático também gera estatísticas (tabela + CSV)? Padrão: sim."""
        if self._scheduler_auto_statistics is None:
            return True
        return self._scheduler_auto_statistics.strip().lower() in ("1", "true", "yes", "sim", "on")

    @property
    def forecast_hours(self) -> list[str]:
        """Horas de previsão (f00–f18) capturadas e processadas. Padrão: todas."""
        if self._forecast_hours:
            hours = [h.strip() for h in self._forecast_hours.split(",") if h.strip()]
            if hours:
                return hours
        return list(FORECAST_HOURS)

    @property
    def pipeline_levels(self) -> list[int]:
        """Níveis (hPa) gerados no pipeline automático (vazio = todos os GRIB)."""
        if self._pipeline_levels:
            levels = []
            for h in self._pipeline_levels.split(","):
                h = h.strip()
                if h.isdigit():
                    levels.append(int(h))
            if levels:
                return levels
        return []

    def ensure_dirs(self) -> None:
        for d in [
            self.dir_gribs,
            self.dir_mapas,
            self.dir_matrizes,
            self.dir_matrizes_predi,
            self.dir_matrizes_bluesky,
            self.dir_analise,
            self.dir_tmp,
        ]:
            d.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_date_subdirs(self, date_str: str, hour: str) -> tuple[Path, Path, Path]:
        grib_dir = self.dir_gribs / date_str / hour
        grib_dir.mkdir(parents=True, exist_ok=True)

        map_dir = self.dir_mapas / date_str / hour
        map_dir.mkdir(parents=True, exist_ok=True)

        mat_dir = self.dir_matrizes / date_str / hour
        mat_dir.mkdir(parents=True, exist_ok=True)

        return grib_dir, map_dir, mat_dir


__all__ = ["Settings"]
