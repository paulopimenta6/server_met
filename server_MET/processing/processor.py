"""Processamento de dados GRIB: seleção de variáveis, extração, unidades, níveis."""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pygrib

from server_MET.acquisition.grib_downloader import get_current_analysis_hour, get_date_str
from server_MET.acquisition.grib_reader import GribReader
from server_MET.core.config import Settings
from server_MET.core.constants import (
    PRESSURE_LEVELS,
    UNITS_MAP,
    VAR_FIXED_LEVEL,
    VAR_MAP,
)

logger = logging.getLogger(__name__)

#: Variáveis com nível de pressão (passíveis de snap de nível).
LEVELED_VARIABLES = ("temp", "nuvem", "umidadeRel", "u", "v", "ozonio")


class DataProcessor:
    def __init__(self, reader: Optional[GribReader] = None) -> None:
        self.settings = Settings()
        self.reader = reader or GribReader()

    def get_current_analysis_hour(self) -> str:
        return get_current_analysis_hour()

    def get_date_str(self) -> str:
        return get_date_str()

    def resolve_level(self, var_name: str, requested_level: Optional[int]) -> Optional[int]:
        if requested_level is None:
            return None
        if var_name in LEVELED_VARIABLES:
            requested_level = int(min(1000, max(1, requested_level)))
            return min(PRESSURE_LEVELS, key=lambda x: abs(x - requested_level))
        if var_name in VAR_FIXED_LEVEL:
            return VAR_FIXED_LEVEL[var_name]
        return requested_level

    def load_gribs(
        self,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast_hours: Optional[list[str]] = None,
    ) -> list[pygrib.gribmessage]:
        date_str = date_str or self.get_date_str()
        analysis = analysis or self.get_current_analysis_hour()

        files = self.reader.find_all_grib_files(date_str, analysis, forecast_hours)
        if not files:
            for alt_analysis in self.reader.find_available_analyses(date_str):
                if alt_analysis == analysis:
                    continue
                files = self.reader.find_all_grib_files(
                    date_str, alt_analysis, forecast_hours
                )
                if files:
                    logger.info(
                        "Fallback: análise %s não encontrada, usando %s",
                        analysis, alt_analysis,
                    )
                    break

        files = self.reader.filter_healthy(files)

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
            raise ValueError(
                f"Variável desconhecida: {var_name}. Opções: {list(VAR_MAP)}"
            )

        name, type_of_level = VAR_MAP[var_name]
        results = []

        # Variáveis com nível fixo (2 m, 10 m, 100 m etc.) ignoram o nível pedido.
        if level is None and var_name in VAR_FIXED_LEVEL:
            level = VAR_FIXED_LEVEL[var_name]

        for grb in grib_objs:
            try:
                if level is not None and type_of_level in (
                    "isobaricInhPa", "isobaricInPa", "heightAboveGround"
                ):
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
                logger.warning("Erro ao selecionar %s: %s", var_name, e)
                continue

            if selected:
                results.append(selected[0])
            else:
                logger.warning("Variável %s não encontrada no nível %s", var_name, level)

        return results

    @staticmethod
    def _normalize_lat(data: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Deixa latitude crescente (S->N) junto com os dados.

        O pygrib devolve linhas do norte (topo) para o sul (base). Para os
        mapas, invertemos ambos (dados e latitude) mantendo-os consistentes —
        sem isso a imagem ficaria com norte/sul trocados em relação ao
        litoral desenhado pelo Cartopy.
        """
        if lat.shape[0] > 1 and lat[0, 0] > lat[-1, 0]:
            data = data[::-1, :]
            lat = lat[::-1, :]
        return data, lat

    def extract_data(
        self,
        grb_msg: pygrib.gribmessage,
        lon_min: float,
        lon_max: float,
        lat_min: float,
        lat_max: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extrai dados da região; lida com regiões que cruzam o meridiano 0°."""
        corrected_lons1, corrected_lons2 = lon_min, lon_max

        if -180 <= lon_min < 0 and -180 <= lon_max < 0:
            corrected_lons1 = lon_min + 360
            corrected_lons2 = lon_max + 360
        elif -180 <= lon_min < 0 and 0 <= lon_max < 180:
            return self._extract_data_split(
                grb_msg, lon_min, lon_max, lat_min, lat_max
            )

        data, lat, lon = grb_msg.data(
            lat1=lat_min, lat2=lat_max,
            lon1=corrected_lons1, lon2=corrected_lons2,
        )
        if lon_min < 0 and lon_max < 0:
            lon = lon - 360

        data, lat = self._normalize_lat(data, lat)
        lon = lon[0, :]
        lat = lat[:, 0]

        return data, lat, lon

    def _extract_data_split(
        self,
        grb_msg: pygrib.gribmessage,
        lons1: float,
        lons2: float,
        lats1: float,
        lats2: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        data_ini, lat_ini, lon_ini = grb_msg.data(
            lat1=lats1, lat2=lats2, lon1=lons1 + 360, lon2=360.0
        )
        lon_ini = lon_ini[0, :] - 360
        data_ini, lat_ini = self._normalize_lat(data_ini, lat_ini)

        data_fim, lat_fim, lon_fim = grb_msg.data(
            lat1=lats1, lat2=lats2, lon1=0.0, lon2=lons2
        )
        lon_fim = lon_fim[0, :]
        data_fim, lat_fim = self._normalize_lat(data_fim, lat_fim)

        lat = lat_ini[:, 0]
        lon = np.append(lon_ini, lon_fim)
        data = np.zeros((data_ini.shape[0], data_ini.shape[1] + data_fim.shape[1]))
        if data_ini.shape[0] == data_fim.shape[0]:
            for i in range(data_ini.shape[0]):
                data[i, :] = np.append(data_ini[i, :], data_fim[i, :])

        return data, lat, lon

    def convert_units(
        self, data: np.ndarray, var_name: str
    ) -> tuple[np.ndarray, str]:
        """Converte unidades GRIB para as unidades de exibição internas."""
        if var_name in ("temp", "temps", "temps2m", "dewpoint2m", "aparente"):
            return data - 273.15, "°C"
        if var_name in ("ps", "prnm"):
            return data / 100, "hPa"
        if var_name in ("chuvaNaoConvec", "chuvaConvec"):
            return data, "mm"
        if var_name in ("precipitacao",):
            # GRIB em kg/m²/s -> mm/h (1 kg/m² = 1 mm).
            return data * 3600, "mm/h"
        if var_name == "neve":
            return data * 100, "cm"
        if var_name == "visibilidade":
            return data / 1000, "km"
        if var_name == "ozonio":
            # Razão de mistura em massa (kg/kg) -> ppb (volume).
            return data * 6.0e8, "ppb"
        return data, UNITS_MAP.get(var_name, "units")

    def close_gribs(self, grib_objs: list[pygrib.gribmessage]) -> None:
        for grb in grib_objs:
            try:
                grb.close()
            except Exception:
                pass


__all__ = ["DataProcessor", "VAR_MAP", "PRESSURE_LEVELS", "VAR_FIXED_LEVEL"]
