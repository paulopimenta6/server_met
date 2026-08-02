"""Gráficos profissionais das análises (perfil vertical, série temporal, histograma).

Seguem os padrões da skill data-visualization: títulos informativos, eixos
rotulados com unidades, paleta colorblind-friendly e alta resolução.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.timeseries import TimeSeriesAnalyzer
from server_MET.core.config import Settings
from server_MET.core.constants import var_label
from server_MET.core.logging_conf import get_logger
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

logger = get_logger(__name__)

# Paleta colorblind-friendly (Okabe-Ito)
C_PRIMARY = "#0072B2"
C_ACCENT = "#D55E00"
C_NEUTRAL = "#999999"


class AnalysisCharts:
    def __init__(self, processor: Optional[DataProcessor] = None) -> None:
        self.settings = Settings()
        self.processor = processor or DataProcessor()
        self.profiles = ProfileAnalyzer(processor)
        self.series = TimeSeriesAnalyzer(processor)
        self.stats = StatisticsAnalyzer(processor)

    def chart(self, kind: str, region: Region, variable: str,
              level: Optional[int] = None, date_str: Optional[str] = None,
              analysis: Optional[str] = None, output_dir: Optional[str] = None,
              title: Optional[str] = None, dpi: int = 150) -> Optional[str]:
        output_dir = Path(output_dir or self.settings.dir_analise)
        output_dir.mkdir(parents=True, exist_ok=True)

        if kind == "profile":
            data = self.profiles.profile(variable, region, date_str, analysis)
            filepath = self._plot_profile(data, output_dir, title, dpi)
        elif kind == "timeseries":
            data = self.series.timeseries(variable, region, level, date_str, analysis)
            filepath = self._plot_timeseries(data, output_dir, title, dpi)
        elif kind == "histogram":
            rows = self.stats.summarize(variable, region, level, date_str, analysis)
            data = rows[0] if rows else {}
            filepath = self._plot_histogram(variable, region, level, date_str, analysis,
                                            data, output_dir, title, dpi)
        else:
            raise ValueError(f"Tipo de gráfico desconhecido: {kind}")

        if filepath:
            logger.info("Gráfico de análise salvo: %s", filepath)
        return filepath

    def _plot_profile(self, data: dict, output_dir: Path, title: Optional[str], dpi: int) -> Optional[str]:
        profile = data.get("profile", [])
        if not profile:
            return None
        levels = [r["level"] for r in profile]
        values = [r["mean"] for r in profile]
        units = profile[0].get("units", "")

        fig, ax = plt.subplots(figsize=(7, 10))
        ax.plot(values, levels, marker="o", color=C_PRIMARY, linewidth=2,
                label=f"{var_label(data['variable'])} ({units})")
        ax.set_ylim(150, 1000)
        ax.set_yscale("log")
        ax.invert_yaxis()
        ax.set_xlabel(f"Valor ({units})")
        ax.set_ylabel("Nível de pressão (hPa)")
        ax.set_title(title or f"Perfil vertical de {var_label(data['variable'])} — {data['region']}",
                     fontweight="bold")
        ax.grid(alpha=0.3)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        name = f"perfil_{data['variable']}_{data['region']}_{data.get('date') or 'semdata'}.png"
        filepath = output_dir / name
        fig.savefig(filepath, bbox_inches="tight", dpi=dpi)
        plt.close(fig)
        return str(filepath)

    def _plot_timeseries(self, data: dict, output_dir: Path, title: Optional[str], dpi: int) -> Optional[str]:
        series = data.get("series", [])
        if not series:
            return None
        xs = [p["forecast"] for p in series]
        ys = [p["value"] for p in series]
        units = data.get("units", "")

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(xs, ys, marker="o", color=C_PRIMARY, linewidth=2,
                label=f"{var_label(data['variable'])} ({units})")
        trend = data.get("trend") or {}
        if trend.get("slope") is not None and trend.get("intercept") is not None:
            xfit = np.array(xs, dtype=float)
            ax.plot(xfit, trend["intercept"] + trend["slope"] * xfit,
                    linestyle="--", color=C_ACCENT, linewidth=1.5,
                    label=f"tendência {trend.get('slope', 0):+.4f} un/h")
        ax.set_xlabel("Hora de previsão (h)")
        ax.set_ylabel(f"Valor ({units})")
        ax.set_xticks(xs)
        ax.set_title(title or f"Série temporal de {var_label(data['variable'])} — {data['region']}",
                     fontweight="bold")
        ax.grid(alpha=0.3)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        name = f"serie_{data['variable']}_{data['region']}_{data.get('date') or 'semdata'}.png"
        filepath = output_dir / name
        fig.savefig(filepath, bbox_inches="tight", dpi=dpi)
        plt.close(fig)
        return str(filepath)

    def _plot_histogram(self, variable: str, region: Region, level: Optional[int],
                        date_str: Optional[str], analysis: Optional[str], summary: dict,
                        output_dir: Path, title: Optional[str], dpi: int) -> Optional[str]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        if not grib_objs:
            return None
        resolved_level = self.processor.resolve_level(variable, level)
        msgs = self.processor.select_variable_from_gribs(grib_objs, variable, resolved_level)
        if not msgs:
            return None
        lon_min, lon_max, lat_min, lat_max = region.bounds
        data, _, _ = self.processor.extract_data(msgs[0], lon_min, lon_max, lat_min, lat_max)
        data, unit = self.processor.convert_units(data, variable)
        flat = np.asarray(data, dtype=float).ravel()
        flat = flat[~np.isnan(flat)]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(flat, bins=30, color=C_PRIMARY, alpha=0.85, edgecolor="white")
        mean_val = float(np.mean(flat))
        median_val = float(np.median(flat))
        ax.axvline(mean_val, color=C_ACCENT, linestyle="--", linewidth=1.5,
                   label=f"Média: {mean_val:.2f}")
        ax.axvline(median_val, color="#009E73", linestyle=":", linewidth=1.5,
                   label=f"Mediana: {median_val:.2f}")
        ax.set_xlabel(f"{var_label(variable)} ({unit})")
        ax.set_ylabel("Frequência")
        ax.set_title(title or f"Distribuição de {var_label(variable)} — {region.full_name}", fontweight="bold")
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        name = f"hist_{variable}_{region.name}_{grib_objs[0].dataDate}.png"
        filepath = output_dir / name
        fig.savefig(filepath, bbox_inches="tight", dpi=dpi)
        plt.close(fig)
        return str(filepath)


__all__ = ["AnalysisCharts"]
