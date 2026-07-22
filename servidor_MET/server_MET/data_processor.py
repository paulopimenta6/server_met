import logging
from typing import Optional

import pygrib
import numpy as np

from server_MET.config import Settings
from server_MET.grib_reader import GribReader

logger = logging.getLogger(__name__)

VAR_MAP: dict[str, tuple[str, str]] = {
    "ps": ("Surface pressure", "surface"),
    "prnm": ("Pressure reduced to MSL", "meanSea"),
    "temp": ("Temperature", "isobaricInhPa"),
    "temps": ("Temperature", "surface"),
    "nuvem": ("Total Cloud Cover", "isobaricInhPa"),
    "chuvaNaoConvec": ("Total Precipitation", "surface"),
    "chuvaConvec": ("Convective precipitation (water)", "surface"),
    "umidadeRel": ("Relative humidity", "isobaricInhPa"),
    "u": ("U component of wind", "isobaricInhPa"),
    "v": ("V component of wind", "isobaricInhPa"),
    "uSupe": ("U component of wind", "heightAboveGround"),
    "vSupe": ("V component of wind", "heightAboveGround"),
}

PRESSURE_LEVELS = [150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000]


class DataProcessor:
    def __init__(self) -> None:
        self.settings = Settings()
        self.reader = GribReader()

    def get_current_analysis_hour(self) -> str:
        import time
        data_horario = time.localtime()
        hora = data_horario.tm_hour
        if hora < 6:
            return "00"
        elif hora < 12:
            return "06"
        elif hora < 18:
            return "12"
        return "18"

    def get_date_str(self) -> str:
        import time
        t = time.localtime()
        return f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"

    def resolve_level(self, var_name: str, requested_level: Optional[int]) -> Optional[int]:
        if requested_level is None:
            return None
        if var_name in ("temp", "nuvem", "umidadeRel", "u", "v"):
            if requested_level < 150:
                return 150
            if requested_level > 1000:
                return 1000
            level = min(PRESSURE_LEVELS, key=lambda x: abs(x - requested_level))
            return level
        return requested_level

    def load_gribs(
        self,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
    ) -> list[pygrib.gribmessage]:
        if date_str is None:
            date_str = self.get_date_str()
        if analysis is None:
            analysis = self.get_current_analysis_hour()
        if forecast_hours is None:
            forecast_hours = ["00", "06", "12", "18"]

        files = self.reader.find_all_grib_files(date_str, analysis, forecast_hours)
        grib_objs = []
        for f in files:
            grb = self.reader.open_grib(f)
            if grb:
                grib_objs.append(grb)
        return grib_objs

    def select_variable_from_gribs(
        self,
        grib_objs: list[pygrib.gribmessage],
        var_name: str,
        level: Optional[int] = None,
    ) -> list:
        if var_name not in VAR_MAP:
            raise ValueError(f"Unknown variable: {var_name}. Options: {list(VAR_MAP.keys())}")

        name, type_of_level = VAR_MAP[var_name]
        results = []

        for grb in grib_objs:
            try:
                if level is not None and type_of_level in ("isobaricInhPa", "isobaricInPa", "heightAboveGround"):
                    selected = grb.select(name=name, typeOfLevel=type_of_level, level=level)
                elif type_of_level in ("surface", "meanSea"):
                    var_list = grb.select(name=name, typeOfLevel=type_of_level)
                    if var_list:
                        lvl = var_list[0].level
                        selected = grb.select(name=name, typeOfLevel=type_of_level, level=lvl)
                    else:
                        selected = []
                else:
                    selected = grb.select(name=name, typeOfLevel=type_of_level)
            except (ValueError, KeyError) as e:
                logger.warning("Error selecting %s: %s", var_name, e)
                continue

            if selected:
                results.append(selected[0])
            else:
                logger.warning("Variable %s not found at level %s", var_name, level)

        return results

    def extract_data(
        self,
        grb_msg: pygrib.gribmessage,
        lon_min: float,
        lon_max: float,
        lat_min: float,
        lat_max: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        lons1, lons2 = lon_min, lon_max
        lats1, lats2 = lat_min, lat_max
        corrected_lons1, corrected_lons2 = lons1, lons2

        if -180 <= lons1 < 0 and -180 <= lons2 < 0:
            corrected_lons1 = lons1 + 360
            corrected_lons2 = lons2 + 360
        elif -180 <= lons1 < 0 and 0 <= lons2 < 180:
            return self._extract_data_split(grb_msg, lons1, lons2, lats1, lats2)

        data, lat, lon = grb_msg.data(
            lat1=lats1, lat2=lats2, lon1=corrected_lons1, lon2=corrected_lons2
        )
        if lons1 < 0 and lons2 < 0:
            lon = lon - 360

        lon = lon[0, :]
        lat = lat[:, 0]
        lat = lat[::-1]

        return data, lat, lon

    def _extract_data_split(
        self,
        grb_msg: pygrib.gribmessage,
        lons1: float,
        lons2: float,
        lats1: float,
        lats2: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        lons1_ini = lons1 + 360
        lons2_ini = 360.0
        lons1_fim = 0.0
        lons2_fim = lons2

        data_ini, lat_ini, lon_ini = grb_msg.data(
            lat1=lats1, lat2=lats2, lon1=lons1_ini, lon2=lons2_ini
        )
        lon_ini = lon_ini[0, :] - 360
        lat_ini = lat_ini[:, 0][::-1]

        data_fim, lat_fim, lon_fim = grb_msg.data(
            lat1=lats1, lat2=lats2, lon1=lons1_fim, lon2=lons2_fim
        )
        lon_fim = lon_fim[0, :]
        lat_fim = lat_fim[:, 0][::-1]

        lat = lat_ini
        lon = np.append(lon_ini, lon_fim)
        data = np.zeros((data_ini.shape[0], data_ini.shape[1] + data_fim.shape[1]))
        if data_ini.shape[0] == data_fim.shape[0]:
            for i in range(data_ini.shape[0]):
                data[i, :] = np.append(data_ini[i, :], data_fim[i, :])

        return data, lat, lon

    def convert_units(
        self, data: np.ndarray, var_name: str
    ) -> tuple[np.ndarray, str]:
        if var_name in ("temp", "temps"):
            return data - 273.15, "°C"
        if var_name in ("ps", "prnm"):
            return data / 100, "hPa"
        if var_name == "chuvaNaoConvec":
            return data, "mm"
        if var_name == "chuvaConvec":
            return data, "mm"
        return data, "units"
