"""Testes offline do dashboard estatístico: repositório `statistics`, CSV,
DashboardAnalyzer e rotas `/analysis/dashboard` + `/analysis/statistics`."""
from __future__ import annotations

import pytest

from server_MET.analysis.dashboard import DashboardAnalyzer
from server_MET.api.dependencies import get_dashboard, get_stats_repo
from server_MET.core.config import Settings
from server_MET.output.statistics import STAT_COLUMNS, StatisticsCSVGenerator
from server_MET.persistence.repositories import StatisticsRepository
from server_MET.processing.regions import Region

SAMPLE_ROW = {
    "variable": "temp",
    "level": 500,
    "units": "K",
    "forecast": 6,
    "date": "20260802",
    "date_str": "20260802",
    "analysis": "06",
    "region": "SP",
    "n_points": 100,
    "n_missing": 0,
    "min": 250.0,
    "max": 260.0,
    "mean": 255.0,
    "median": 255.0,
    "std": 2.0,
    "iqr": 3.0,
    "p1": 250.5,
    "p5": 251.0,
    "p25": 253.0,
    "p50": 255.0,
    "p75": 257.0,
    "p95": 259.0,
    "p99": 259.5,
    "skewness": 0.1,
    "kurtosis": -0.2,
}


def _rows(n=3, base=0):
    rows = []
    for i in range(n):
        r = dict(SAMPLE_ROW)
        r["forecast"] = base + i * 6
        r["mean"] = 255.0 + i
        rows.append(r)
    return rows


class TestStatisticsRepository:
    def test_save_query_delete_count(self, isolated_db):
        repo = StatisticsRepository()
        assert repo.count() == 0
        saved = repo.save_many(_rows())
        assert saved == 3
        assert repo.count() == 3

        queried = repo.query(variable="temp", region="SP")
        assert len(queried) == 3
        assert {q["forecast"] for q in queried} == {0, 6, 12}
        assert queried[0]["mean"] == 255.0

        filtered = repo.query(variable="temp", region="SP", level=500, date_str="20260802", analysis="06")
        assert len(filtered) == 3

        wrong = repo.query(variable="temp", region="RJ")
        assert wrong == []

        deleted = repo.delete("temp", "SP", "20260802", "06")
        assert deleted == 3
        assert repo.count() == 0

    def test_save_many_empty(self, isolated_db):
        repo = StatisticsRepository()
        assert repo.save_many([]) == 0

    def test_roundtrip_real_values(self, isolated_db):
        repo = StatisticsRepository()
        repo.save_many(_rows())
        row = repo.query(variable="temp", region="SP")[0]
        assert row["p1"] == pytest.approx(250.5)
        assert row["skewness"] == pytest.approx(0.1)


class TestStatisticsCSVGenerator:
    def test_generate_writes_csv(self, isolated_db, tmp_path, monkeypatch):
        settings = Settings()
        monkeypatch.setattr(type(settings), "dir_analise", property(lambda self: tmp_path))

        gen = StatisticsCSVGenerator()
        region = Region(name="SP")
        filepath = gen.generate(_rows(), region, "temp", 500, "20260802", "06")

        assert filepath is not None
        path = Settings().dir_analise / filepath.rsplit("/", 1)[-1]
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert content.splitlines()[0].rstrip() == ",".join(STAT_COLUMNS)
        assert content.count("temp") == 3  # 3 linhas de dados
        assert "20260802" in content

    def test_generate_empty_returns_none(self, isolated_db):
        gen = StatisticsCSVGenerator()
        assert gen.generate([], Region(name="SP"), "temp", None) is None

    def test_generate_registers_output(self, isolated_db, tmp_path, monkeypatch):
        from server_MET.core.config import Settings as S

        settings = S()
        monkeypatch.setattr(type(settings), "dir_analise", property(lambda self: tmp_path))
        from server_MET.persistence.repositories import OutputRepository

        gen = StatisticsCSVGenerator()
        gen.generate(_rows(), Region(name="SP"), "temp", 500, "20260802", "06")
        outputs = OutputRepository().list()
        assert any(o["kind"] == "statistics" for o in outputs)


class TestDashboardAnalyzer:
    def _fakes(self, summary, trend, profile):
        class FakeProcessor:
            def __init__(self):
                self.reader = FakeReader()

        class FakeReader:
            def latest_available_cycle(self, *a, **k):
                return ("20260802", "06")

        class FakeStatistics:
            def __init__(self, rows):
                self.rows = rows

            def summarize(self, *a, **k):
                return self.rows

        class FakeSeries:
            def timeseries(self, *a, **k):
                return {"trend": trend, "series": [1]}

        class FakeProfiles:
            def profile(self, *a, **k):
                return profile

        class FakeCsv:
            def __init__(self):
                self.calls = []

            def generate(self, rows, region, var, level, date, ana):
                self.calls.append((rows, region, var, level, date, ana))
                return "data/analise/fake_stats.csv"

        csv = FakeCsv()
        dashboard = DashboardAnalyzer(
            processor=FakeProcessor(),
            statistics=FakeStatistics(summary),
            series=FakeSeries(),
            profiles=FakeProfiles(),
            csv_gen=csv,
        )
        return dashboard, csv

    def test_build_persists_and_returns(self, isolated_db):
        summary = _rows()
        trend = {"slope": 1.0, "p_value": 0.01, "significant": True,
                 "direction": "crescente", "r_squared": 0.9}
        dashboard, csv = self._fakes(summary, trend, {"profile": []})

        result = dashboard.build("temp", Region(name="SP"), 500, "20260802", "06")

        assert result["summary"] == summary
        assert result["trend"]["slope"] == 1.0
        assert result["profile"] is None
        assert result["csv"] == "data/analise/fake_stats.csv"

        assert StatisticsRepository().count() == 3
        assert len(csv.calls) == 1

    def test_build_empty_returns_none(self, isolated_db):
        dashboard, _ = self._fakes([], {}, {"profile": []})
        assert dashboard.build("temp", Region(name="SP"), 500, "20260802", "06") is None
        assert StatisticsRepository().count() == 0


@pytest.mark.asyncio
async def test_get_statistics_route(client, isolated_db):
    from server_MET.persistence.repositories import StatisticsRepository

    StatisticsRepository().save_many(_rows())
    response = await client.get("/analysis/statistics", params={"variable": "temp", "region": "SP"})
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert {r["forecast"] for r in data["rows"]} == {0, 6, 12}


@pytest.mark.asyncio
async def test_dashboard_route_post_and_cache(client, isolated_db):
    from server_MET.api.app import app

    class StubDashboard:
        def __init__(self):
            self.processor = self._processor()

        class _processor:
            class _reader:
                @staticmethod
                def latest_available_cycle(*a, **k):
                    return ("20260802", "06")

            reader = _reader

        @staticmethod
        def build(*a, **k):
            return {"variable": "temp", "region": "SP", "level": 500,
                    "date": "20260802", "analysis": "06",
                    "summary": _rows(), "trend": {"slope": 1.0},
                    "profile": None, "csv": "data/analise/fake.csv"}

    app.dependency_overrides[get_dashboard] = lambda: StubDashboard()
    try:
        response = await client.post("/analysis/dashboard", json={
            "variable": "temp", "region": "SP", "level": 500,
        })
        assert response.status_code == 200
        body = response.json()
        assert body["summary"][0]["forecast"] == 0

        cached = await client.get(
            "/analysis/dashboard",
            params={"variable": "temp", "region": "SP", "level": 500},
        )
        assert cached.status_code == 200
        assert cached.json()["date"] == "20260802"
    finally:
        app.dependency_overrides.pop(get_dashboard, None)


@pytest.mark.asyncio
async def test_dashboard_route_not_found(client, isolated_db):
    response = await client.get("/analysis/dashboard", params={"variable": "temp", "region": "SP"})
    assert response.status_code == 404
