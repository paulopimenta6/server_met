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


def _skewness(values: np.ndarray) -> float:
    """Assimetria (Fisher). Prefere scipy quando disponível."""
    try:
        from scipy.stats import skew

        return round(float(skew(values, bias=False)), 4)
    except ImportError:
        n = int(values.size)
        if n < 3:
            return 0.0
        mean = float(values.mean())
        m2 = float(((values - mean) ** 2).sum()) / n
        m3 = float(((values - mean) ** 3).sum()) / n
        if m2 <= 0:
            return 0.0
        return round(float(m3 / m2 ** 1.5), 4)


def _kurtosis(values: np.ndarray) -> float:
    """Curtose excessiva (Fisher). Prefere scipy quando disponível."""
    try:
        from scipy.stats import kurtosis

        return round(float(kurtosis(values, bias=False)), 4)
    except ImportError:
        n = int(values.size)
        if n < 4:
            return 0.0
        mean = float(values.mean())
        m2 = float(((values - mean) ** 2).sum()) / n
        m4 = float(((values - mean) ** 4).sum()) / n
        if m2 <= 0:
            return 0.0
        return round(float(m4 / m2 ** 2 - 3.0), 4)


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
                    "skewness": _skewness(valid),
                    "kurtosis": _kurtosis(valid),
                    **percentiles,
                }
            )
        return results


__all__ = ["StatisticsAnalyzer"]
