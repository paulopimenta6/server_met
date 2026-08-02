"""Testes da captação contínua (scheduler) e do estado de ingestão."""
from __future__ import annotations

from datetime import datetime

from server_MET.acquisition.scheduler import (
    SchedulerRunner,
    latest_published_cycle,
    previous_cycle,
)
from server_MET.persistence.repositories import IngestStateRepository


class TestCycleHelpers:
    def test_latest_published_cycle(self):
        date_str, ana = latest_published_cycle(datetime(2026, 7, 31, 14, 30))
        assert date_str == "20260731"
        assert ana == "06"

    def test_latest_published_cycle_night(self):
        date_str, ana = latest_published_cycle(datetime(2026, 8, 1, 3, 0))
        assert date_str == "20260731"
        assert ana == "18"

    def test_previous_cycle(self):
        assert previous_cycle("20260731", "00") == ("20260730", "18")
        assert previous_cycle("20260731", "12") == ("20260731", "06")


class FakeDownloader:
    """Substituto do GribDownloader: retorna arquivos 'baixados' sem rede."""

    def __init__(self, files=None) -> None:
        self.files = files or {"0p25": ["/fake/gfs.t06z.pgrb2.0p25.f000"]}
        self.calls: list[tuple] = []

    def download_gribs_all_resolutions(self, date_str, analysis_hour, **kwargs):
        self.calls.append((date_str, analysis_hour))
        return self.files


class TestSchedulerRunner:
    def test_process_new_cycles_downloads_and_pipelines(self, isolated_db):
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        ran = []
        runner._run_pipeline = lambda date, ana: ran.append((date, ana))

        import asyncio

        asyncio.run(runner._process_new_cycles())

        assert len(fake.calls) >= 1
        assert ran, "pipeline deveria ter rodado"
        state = runner.state.get_json("processed_cycles", [])
        assert f"{ran[0][0]}_{ran[0][1]}" in state

    def test_process_new_cycles_skips_already_processed(self, isolated_db):
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        target = latest_published_cycle()
        prev = previous_cycle(*target)
        runner.state.set_json(
            "processed_cycles",
            [f"{target[0]}_{target[1]}", f"{prev[0]}_{prev[1]}"],
        )
        runner._run_pipeline = lambda date, ana: None

        import asyncio

        asyncio.run(runner._process_new_cycles())

        assert fake.calls == []

    def test_status_shape(self, isolated_db):
        runner = SchedulerRunner()
        status = runner.status()
        assert status["enabled"] is True
        assert "grib_interval_min" in status
        assert "last_grib_check" in status


class TestIngestStateRepository:
    def test_roundtrip(self, isolated_db):
        repo = IngestStateRepository()
        repo.set("key_a", "valor")
        assert repo.get("key_a") == "valor"
        repo.set_json("lista", [1, 2, 3])
        assert repo.get_json("lista") == [1, 2, 3]
        assert repo.get_json("inexistente", "padrao") == "padrao"

    def test_all(self, isolated_db):
        repo = IngestStateRepository()
        repo.set("a", "1")
        repo.set("b", "2")
        assert repo.all() == {"a": "1", "b": "2"}
