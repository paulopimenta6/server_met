"""Testes da camada de análise (offline): estatísticas, perfis, séries e gráficos."""
import numpy as np

from server_MET.analysis.charts import AnalysisCharts
from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.timeseries import TimeSeriesAnalyzer
from server_MET.processing.regions import Region


class TestStatisticsAnalyzer:
    def test_summarize_without_grib_returns_empty(self, isolated_db):
        analyzer = StatisticsAnalyzer()
        result = analyzer.summarize("temp", Region(name="SP"), 500, "20990101", "06")
        assert result == []


class TestProfileAnalyzer:
    def test_profile_without_grib_returns_empty_profile(self, isolated_db):
        analyzer = ProfileAnalyzer()
        result = analyzer.profile("temp", Region(name="SP"), "20990101", "06")
        assert result["profile"] == []
        assert result["variable"] == "temp"


class TestTimeSeriesAnalyzer:
    def test_timeseries_without_grib(self, isolated_db):
        analyzer = TimeSeriesAnalyzer()
        result = analyzer.timeseries("temp", Region(name="SP"), 500, "20990101", "06")
        assert result["series"] == []

    def test_fit_trend_single_point(self, isolated_db):
        analyzer = TimeSeriesAnalyzer()
        trend = analyzer._fit_trend([{"forecast": 0, "value": 10.0}])
        assert trend["slope"] is None

    def test_fit_trend_positive_slope(self, isolated_db):
        analyzer = TimeSeriesAnalyzer()
        points = [{"forecast": f, "value": 10 + 2.0 * f} for f in (0, 6, 12, 18)]
        trend = analyzer._fit_trend(points)
        assert trend["slope"] is not None
        assert trend["slope"] > 0
        assert trend["r_squared"] > 0.99
        assert trend["significant"] is True
        assert trend["direction"] == "crescente"

    def test_fit_trend_negative_slope(self, isolated_db):
        analyzer = TimeSeriesAnalyzer()
        points = [{"forecast": f, "value": 100 - 3.0 * f} for f in (0, 6, 12, 18)]
        trend = analyzer._fit_trend(points)
        assert trend["slope"] < 0
        assert trend["direction"] == "decrescente"


class TestAnalysisCharts:
    def test_chart_invalid_kind(self, isolated_db):
        import pytest

        charts = AnalysisCharts()
        with pytest.raises(ValueError):
            charts.chart("bogus", Region(name="SP"), "temp", 500, "20990101", "06")

    def test_chart_profile_without_data_returns_none(self, isolated_db, tmp_path):
        charts = AnalysisCharts()
        result = charts.chart(
            "profile", Region(name="SP"), "temp", 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert result is None
