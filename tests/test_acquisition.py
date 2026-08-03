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
        self.calls.append((date_str, analysis_hour, kwargs))
        return self.files


class TestSchedulerRunner:
    def test_process_new_cycles_downloads_and_pipelines(self, isolated_db):
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        ran = []
        runner._run_pipeline = lambda date, ana, proc=None: ran.append((date, ana))
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (True, [])

        import asyncio

        asyncio.run(runner._process_new_cycles())

        assert len(fake.calls) >= 1
        assert ran, "pipeline deveria ter rodado"
        state = runner.state.get_json("processed_cycles", [])
        assert f"{ran[0][0]}_{ran[0][1]}" in state

    def test_process_new_cycles_partial_forecast_not_marked(self, isolated_db):
        """Ciclo com previsão parcial/incompleta NÃO é marcado como processado."""
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        ran = []
        runner._run_pipeline = lambda date, ana, proc=None: ran.append((date, ana))
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (False, ["06"])

        import asyncio

        asyncio.run(runner._process_new_cycles())

        assert ran == [], "pipeline não deveria rodar com previsão incompleta"
        state = runner.state.get_json("processed_cycles", [])
        assert state == []
        assert runner.state.get("last_pipeline_cycle") is None

    def test_process_new_cycles_uses_configured_resolution(self, isolated_db):
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        runner.settings._scheduler_resolution = "0p50"
        runner._run_pipeline = lambda date, ana, proc=None: None
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (True, [])

        import asyncio

        asyncio.run(runner._process_new_cycles())

        assert fake.calls
        _, _, kwargs = fake.calls[0]
        assert kwargs.get("resolutions") == ["0p50"]

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
        runner._run_pipeline = lambda date, ana, proc=None: None

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


class TestGribDownloaderExistingFiles:
    """A2: arquivo existente não é confiado cegamente — valida antes de pular."""

    def _paths(self):
        from server_MET.core.config import Settings

        dest = Settings().dir_gribs / "20260801" / "06"
        dest.mkdir(parents=True, exist_ok=True)
        return dest / "gfs.t06z.pgrb2.0p25.f000"

    def test_existing_validated_file_skipped(self, isolated_db, isolated_data_dirs, monkeypatch):
        from server_MET.acquisition.grib_downloader import GribDownloader

        d = GribDownloader()
        fp = self._paths()
        fp.write_bytes(b"data")
        d.repo.register("20260801", "06", "0p25", "00", fp)
        d.repo.mark("20260801", "06", "0p25", "00", "downloaded", file_size=4)

        monkeypatch.setattr(
            d, "validate_grib",
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria validar")),
        )
        files = d.download_gribs(
            date_str="20260801", analysis_hour="06",
            forecast_hours=["00"], resolution="0p25",
        )
        assert files == [fp]
        assert d.repo.get("20260801", "06", "0p25", "00")["status"] == "skipped"

    def test_existing_unvalidated_file_is_validated(self, isolated_db, isolated_data_dirs, monkeypatch):
        from server_MET.acquisition.grib_downloader import GribDownloader

        d = GribDownloader()
        fp = self._paths()
        fp.write_bytes(b"data")

        monkeypatch.setattr(d, "validate_grib", lambda *a, **k: True)
        files = d.download_gribs(
            date_str="20260801", analysis_hour="06",
            forecast_hours=["00"], resolution="0p25",
        )
        assert files == [fp]
        assert d.repo.get("20260801", "06", "0p25", "00")["status"] == "downloaded"

    def test_existing_corrupted_file_removed_and_redownloaded(self, isolated_db, isolated_data_dirs, monkeypatch):
        from server_MET.acquisition.grib_downloader import GribDownloader

        d = GribDownloader()
        fp = self._paths()
        fp.write_bytes(b"parcial")

        monkeypatch.setattr(d, "validate_grib", lambda *a, **k: False)
        monkeypatch.setattr(d, "check_url_exists", lambda *a, **k: False)
        files = d.download_gribs(
            date_str="20260801", analysis_hour="06",
            forecast_hours=["00"], resolution="0p25",
        )
        assert files == []
        assert not fp.exists(), "arquivo corrompido deveria ter sido removido"
        assert d.repo.get("20260801", "06", "0p25", "00")["status"] == "failed"
