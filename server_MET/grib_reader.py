import logging
from pathlib import Path
from typing import Optional

import pygrib

from server_MET.config import Settings

logger = logging.getLogger(__name__)


class GribReader:
    SUPPORTED_RESOLUTIONS = ["0p25", "0p50", "1p00"]

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
            logger.warning("Directory not found: %s", base_dir)
            return None

        resolutions = (
            [resolution]
            if resolution
            else self.SUPPORTED_RESOLUTIONS
        )
        for res in resolutions:
            for f in base_dir.iterdir():
                if f.is_file() and f.name.endswith(f".f0{forecast}") and res in f.name:
                    logger.info("Found GRIB file: %s", f)
                    return f
        logger.warning(
            "No GRIB file found for %s %s f%02s", date_str, analysis, forecast
        )
        return None

    def find_all_grib_files(
        self,
        date_str: str,
        analysis: str,
        forecast_hours: Optional[list[str]] = None,
    ) -> list[Path]:
        if forecast_hours is None:
            forecast_hours = ["00", "06", "12", "18"]
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
            logger.error("Failed to open GRIB file %s: %s", filepath, e)
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
            logger.warning("Variable not found: %s at %s/%s", name, type_of_level, level)
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

    def get_data(
        self,
        grb: pygrib.gribmessage,
        lat1: float,
        lat2: float,
        lon1: float,
        lon2: float,
    ) -> tuple:
        return grb.data(lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2)
