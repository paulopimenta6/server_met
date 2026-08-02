"""Leitura de arquivos GRIB2 com pygrib."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pygrib

from server_MET.core.config import Settings
from server_MET.core.constants import RESOLUTIONS

logger = logging.getLogger(__name__)


class GribReader:
    def __init__(self) -> None:
        self.settings = Settings()

    def find_grib_file(
        self,
        date_str: str,
        analysis: str,
        forecast: str,
        resolution: Optional[str] = None,
    ) -> Optional[Path]:
        base_dir = self.settings.dir_gribs / date_str / analysis
        if not base_dir.exists():
            logger.warning("Diretório não encontrado: %s", base_dir)
            return None

        resolutions = [resolution] if resolution else RESOLUTIONS
        for res in resolutions:
            for f in base_dir.iterdir():
                if f.is_file() and f.name.endswith(f".f0{forecast}") and res in f.name:
                    logger.info("Arquivo GRIB encontrado: %s", f)
                    return f
        logger.warning("Nenhum arquivo GRIB para %s %s f%02s", date_str, analysis, int(forecast))
        return None

    def find_available_analyses(self, date_str: str) -> list[str]:
        base_dir = self.settings.dir_gribs / date_str
        if not base_dir.exists():
            return []
        return sorted(d.name for d in base_dir.iterdir() if d.is_dir())

    def find_available_resolutions(self, date_str: str, analysis: str) -> list[str]:
        base_dir = self.settings.dir_gribs / date_str / analysis
        if not base_dir.exists():
            return []
        found: set[str] = set()
        for f in base_dir.iterdir():
            if not f.is_file():
                continue
            for res in RESOLUTIONS:
                if res in f.name:
                    found.add(res)
        return sorted(found)

    def find_all_grib_files(
        self,
        date_str: str,
        analysis: str,
        forecast_hours: Optional[list[str]] = None,
    ) -> list[Path]:
        if forecast_hours is None:
            forecast_hours = self.settings.forecast_hours
        files = []
        for fh in forecast_hours:
            f = self.find_grib_file(date_str, analysis, fh)
            if f:
                files.append(f)
        return files

    def open_grib(self, filepath: Path) -> Optional[pygrib.gribmessage]:
        try:
            return pygrib.open(str(filepath))
        except (OSError, ValueError) as e:
            logger.error("Falha ao abrir GRIB %s: %s", filepath, e)
            return None

    def select_variable(
        self,
        grb: pygrib.gribmessage,
        name: str,
        type_of_level: str,
        level: Optional[int] = None,
    ) -> list:
        try:
            if level is not None:
                return grb.select(name=name, typeOfLevel=type_of_level, level=level)
            return grb.select(name=name, typeOfLevel=type_of_level)
        except (ValueError, KeyError) as e:
            logger.warning("Variável não encontrada: %s em %s/%s (%s)", name, type_of_level, level, e)
            return []

    def list_variables(self, filepath: Path) -> list[dict]:
        grb = self.open_grib(filepath)
        if grb is None:
            return []
        variables = []
        try:
            for g in grb:
                variables.append(
                    {
                        "name": g.name,
                        "type_of_level": g.typeOfLevel,
                        "level": g.level,
                        "units": g.units,
                        "forecast_time": g.forecastTime,
                        "data_date": g.dataDate,
                    }
                )
        finally:
            grb.close()
        return variables


__all__ = ["GribReader"]
