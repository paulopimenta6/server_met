"""Dashboard estatístico consolidado de uma região.

Reúne, para uma variável/nível/ciclo:
- resumo descritivo por hora de previsão (média, mediana, percentis, desvio…);
- tendência por regressão linear (statsmodels OLS com IC da inclinação e
  teste de normalidade dos resíduos);
- perfil vertical (quando a variável é de nível de pressão);
- gravação no banco (tabela `statistics`) e exportação em CSV (`dir_analise`),
  disponíveis também pela API REST.
"""
from __future__ import annotations

from typing import Optional

from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.timeseries import TimeSeriesAnalyzer
from server_MET.core.logging_conf import get_logger
from server_MET.output.statistics import StatisticsCSVGenerator
from server_MET.persistence.repositories import StatisticsRepository
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

logger = get_logger(__name__)


class DashboardAnalyzer:
    """Consolida as análises estatísticas de uma variável sobre a região."""

    def __init__(
        self,
        processor: Optional[DataProcessor] = None,
        statistics: Optional[StatisticsAnalyzer] = None,
        series: Optional[TimeSeriesAnalyzer] = None,
        profiles: Optional[ProfileAnalyzer] = None,
        stats_repo: Optional[StatisticsRepository] = None,
        csv_gen: Optional[StatisticsCSVGenerator] = None,
    ) -> None:
        self.processor = processor or DataProcessor()
        self.statistics = statistics or StatisticsAnalyzer(self.processor)
        self.series = series or TimeSeriesAnalyzer(self.processor)
        self.profiles = profiles or ProfileAnalyzer(self.processor)
        self.stats_repo = stats_repo or StatisticsRepository()
        self.csv_gen = csv_gen or StatisticsCSVGenerator()

    def build(
        self,
        var_name: str,
        region: Region,
        level: Optional[int] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> Optional[dict]:
        summary = self.statistics.summarize(var_name, region, level, date_str, analysis)
        if not summary:
            logger.warning("Dashboard sem dados GRIB para %s/%s", var_name, region.name)
            return None

        resolved_level = summary[0].get("level")
        units = summary[0].get("units", "")

        series_data = self.series.timeseries(var_name, region, resolved_level, date_str, analysis)
        profile_data = self.profiles.profile(var_name, region, date_str, analysis)

        # Persistência no banco (tabela `statistics`).
        rows = []
        for r in summary:
            row = dict(r)
            row["date_str"] = date_str or r.get("date")
            row["analysis"] = analysis or ""
            rows.append(row)
        try:
            self.stats_repo.delete(var_name, region.name, date_str or "", analysis or "", resolved_level)
            self.stats_repo.save_many(rows)
        except Exception as e:  # nunca derruba o dashboard
            logger.warning("Falha ao persistir estatísticas de %s: %s", var_name, e)

        # Exportação CSV (dir_analise).
        csv_path = None
        try:
            csv_path = self.csv_gen.generate(
                rows, region, var_name, resolved_level, date_str, analysis
            )
        except Exception as e:
            logger.warning("Falha ao gerar CSV de estatísticas de %s: %s", var_name, e)

        return {
            "variable": var_name,
            "region": region.name,
            "level": resolved_level,
            "date": date_str or (summary[0].get("date") if summary else None),
            "analysis": analysis,
            "units": units,
            "summary": summary,
            "trend": series_data.get("trend") or {},
            "profile": profile_data if profile_data.get("profile") else None,
            "csv": csv_path,
        }


__all__ = ["DashboardAnalyzer"]
