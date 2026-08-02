"""Perfil vertical: valor da variável em todos os níveis de pressão (150–1000 hPa).

Para `temp`, `umidadeRel`, `u`, `v` e `wind` a análise é por nível isobárico;
para variáveis de superfície retorna apenas o nível de superfície.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from server_MET.core.constants import PRESSURE_LEVELS, UNITS_MAP
from server_MET.core.logging_conf import get_logger
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

logger = get_logger(__name__)

#: Variáveis passíveis de perfil vertical por nível de pressão.
PROFILE_VARIABLES = ("temp", "umidadeRel", "u", "v", "wind")


class ProfileAnalyzer:
    """Perfil vertical de uma variável (média espacial sobre a região)."""

    def __init__(self, processor: Optional[DataProcessor] = None) -> None:
        self.processor = processor or DataProcessor()

    def profile(
        self,
        var_name: str,
        region: Region,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> dict:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            logger.warning("Nenhum dado GRIB carregado para perfil vertical")
            return {"profile": [], "variable": var_name, "region": region.name}

        lon_min, lon_max, lat_min, lat_max = region.bounds
        base_var = "u" if var_name == "wind" else var_name
        levels = PRESSURE_LEVELS if base_var in PROFILE_VARIABLES else [None]

        data_date = None
        rows = []
        for level in levels:
            msgs = self.processor.select_variable_from_gribs(grib_objs, base_var, level)
            if not msgs:
                continue
            if data_date is None:
                data_date = msgs[0].dataDate
            msg = msgs[0]
            data, _, _ = self.processor.extract_data(
                msg, lon_min, lon_max, lat_min, lat_max
            )
            data, unit = self.processor.convert_units(data, base_var)
            valid = np.asarray(data, dtype=float).ravel()
            valid = valid[~np.isnan(valid)]

            if var_name == "wind":
                v_msgs = self.processor.select_variable_from_gribs(grib_objs, "v", level)
                if v_msgs:
                    data_v, _, _ = self.processor.extract_data(
                        v_msgs[0], lon_min, lon_max, lat_min, lat_max
                    )
                    vv = np.asarray(data_v, dtype=float).ravel()
                    value = float(np.nanmean(np.sqrt(valid**2 + vv**2)))
                    unit = "m/s"
                else:
                    value = float(np.nanmean(valid))
            else:
                value = float(np.nanmean(valid)) if valid.size else None

            rows.append(
                {
                    "level": level,
                    "value": round(value, 4) if value is not None else None,
                    "mean": round(float(np.nanmean(valid)), 4) if valid.size else None,
                    "min": round(float(np.nanmin(valid)), 4) if valid.size else None,
                    "max": round(float(np.nanmax(valid)), 4) if valid.size else None,
                    "units": unit,
                }
            )

        return {
            "variable": var_name,
            "region": region.name,
            "date": data_date,
            "analysis": analysis,
            "levels": [r["level"] for r in rows],
            "profile": rows,
        }


__all__ = ["ProfileAnalyzer"]
