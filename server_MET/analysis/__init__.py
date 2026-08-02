"""Camada de análise de dados meteorológicos.

Módulos:
- statistics: resumo descritivo de uma variável em uma região.
- profiles: perfil vertical (variável por nível de pressão).
- timeseries: evolução nas horas de previsão com tendência linear.
- charts: gráficos profissionais (PNG) das análises.
- summary: orquestração e consolidação por região.
"""
from __future__ import annotations

from server_MET.analysis.charts import AnalysisCharts
from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.summary import RegionSummary
from server_MET.analysis.timeseries import TimeSeriesAnalyzer

__all__ = [
    "AnalysisCharts",
    "ProfileAnalyzer",
    "StatisticsAnalyzer",
    "RegionSummary",
    "TimeSeriesAnalyzer",
]
