"""Série temporal da variável nas horas de previsão + regressão linear de tendência.

Usa statsmodels (OLS) para estimar tendência com p-valor e R², permitindo
verificar se a variável sobe/desce de forma estatisticamente significativa.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from server_MET.core.constants import UNITS_MAP
from server_MET.core.logging_conf import get_logger
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

logger = get_logger(__name__)


class TimeSeriesAnalyzer:
    """Evolução da média espacial da variável nas horas de previsão (f00–f18)."""

    def __init__(self, processor: Optional[DataProcessor] = None) -> None:
        self.processor = processor or DataProcessor()

    def timeseries(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> dict:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            logger.warning("Nenhum dado GRIB carregado para série temporal")
            return {"series": [], "variable": var_name, "region": region.name}

        lon_min, lon_max, lat_min, lat_max = region.bounds
        base_var = "u" if var_name == "wind" else var_name
        resolved_level = self.processor.resolve_level(base_var, level)

        msgs = self.processor.select_variable_from_gribs(
            grib_objs, base_var, resolved_level
        )
        data_date = msgs[0].dataDate if msgs else None

        points = []
        for msg in msgs:
            data, _, _ = self.processor.extract_data(
                msg, lon_min, lon_max, lat_min, lat_max
            )
            data, unit = self.processor.convert_units(data, base_var)
            valid = np.asarray(data, dtype=float).ravel()
            valid = valid[~np.isnan(valid)]
            points.append(
                {
                    "forecast": int(msg.forecastTime),
                    "value": round(float(np.nanmean(valid)), 4) if valid.size else None,
                }
            )

        points.sort(key=lambda p: p["forecast"])
        trend = self._fit_trend(points)

        return {
            "variable": var_name,
            "level": resolved_level,
            "region": region.name,
            "date": data_date,
            "analysis": analysis,
            "units": unit,
            "series": points,
            "trend": trend,
        }

    def _fit_trend(self, points: list[dict]) -> dict:
        if len(points) < 2:
            return {"slope": None, "intercept": None, "p_value": None, "r_squared": None,
                    "slope_ci": None, "jarque_bera_p": None, "note": "menos de 2 pontos"}

        x = np.array([p["forecast"] for p in points], dtype=float)
        y = np.array([p["value"] for p in points], dtype=float)
        if np.isnan(y).any():
            return {"slope": None, "intercept": None, "p_value": None, "r_squared": None,
                    "slope_ci": None, "jarque_bera_p": None, "note": "valores ausentes"}

        try:
            import statsmodels.api as sm
            from statsmodels.stats.stattools import jarque_bera

            X = sm.add_constant(x)
            model = sm.OLS(y, X).fit(cov_type="HC3")
            conf = model.conf_int(alpha=0.05)
            _, jb_p, _, _ = jarque_bera(model.resid)
            return {
                "slope": round(float(model.params[1]), 6),
                "intercept": round(float(model.params[0]), 6),
                "p_value": round(float(model.pvalues[1]), 6),
                "r_squared": round(float(model.rsquared), 6),
                "slope_ci": [round(float(conf[1, 0]), 6), round(float(conf[1, 1]), 6)],
                "jarque_bera_p": round(float(jb_p), 6),
                "significant": bool(model.pvalues[1] < 0.05),
                "direction": (
                    "crescente" if model.params[1] > 0 else "decrescente"
                ) if model.pvalues[1] < 0.05 else "sem tendência significativa",
                "n_points": int(len(points)),
            }
        except ImportError:
            slope = np.polyfit(x, y, 1)[0]
            return {
                "slope": round(float(slope), 6),
                "intercept": None,
                "p_value": None,
                "r_squared": None,
                "slope_ci": None,
                "jarque_bera_p": None,
                "significant": None,
                "direction": "crescente" if slope > 0 else "decrescente",
                "n_points": int(len(points)),
                "note": "statsmodels indisponível; tendência por polyfit",
            }


__all__ = ["TimeSeriesAnalyzer"]
