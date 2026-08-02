"""Estatística descritiva de variáveis meteorológicas por região."""
from __future__ import annotations

from typing import Optional

import numpy as np

from server_MET.core.constants import UNITS_MAP, VAR_MAP
from server_MET.core.logging_conf import get_logger
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

logger = get_logger(__name__)

_PERCENTILES = [1, 5, 25, 50, 75, 95, 99]


class StatisticsAnalyzer:
    """Resumo estatístico de uma variável na região, por hora de previsão."""

    def __init__(self, processor: Optional[DataProcessor] = None) -> None:
        self.processor = processor or DataProcessor()

    def summarize(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> list[dict]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            logger.warning("Nenhum dado GRIB carregado para estatísticas")
            return []

        resolved_level = self.processor.resolve_level(var_name, level)
        var_msgs = self.processor.select_variable_from_gribs(
            grib_objs, var_name, resolved_level
        )

        lon_min, lon_max, lat_min, lat_max = region.bounds
        results = []
        for msg in var_msgs:
            data, lat, lon = self.processor.extract_data(
                msg, lon_min, lon_max, lat_min, lat_max
            )
            data, unit = self.processor.convert_units(data, var_name)

            flat = np.asarray(data, dtype=float).ravel()
            valid = flat[~np.isnan(flat)]

            percentiles = {
                f"p{p}": round(float(np.percentile(valid, p)), 4)
                for p in _PERCENTILES
            }

            results.append(
                {
                    "variable": var_name,
                    "level": resolved_level,
                    "units": unit,
                    "forecast": msg.forecastTime,
                    "date": msg.dataDate,
                    "region": region.name,
                    "n_points": int(valid.size),
                    "n_missing": int(np.isnan(flat).sum()),
                    "min": round(float(valid.min()), 4),
                    "max": round(float(valid.max()), 4),
                    "mean": round(float(valid.mean()), 4),
                    "median": round(float(np.median(valid)), 4),
                    "std": round(float(valid.std()), 4),
                    "iqr": round(float(np.percentile(valid, 75) - np.percentile(valid, 25)), 4),
                    **percentiles,
                }
            )
        return results


__all__ = ["StatisticsAnalyzer"]
