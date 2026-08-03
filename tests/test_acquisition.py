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

    def test_initial_acquisition_downloads_and_metar(self, isolated_db):
        """Captação inicial bloqueante obtém GRIB completo (00/06/12/18) + METAR."""
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        runner.settings._scheduler_resolution = "0p50"
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (True, [])
        runner.metar.get_all_metars = lambda: [{"station": "SBGR"}]

        import asyncio

        summary = asyncio.run(runner.initial_acquisition())

        assert fake.calls, "deveria ter tentado baixar GRIB"
        _, _, kwargs = fake.calls[0]
        assert kwargs.get("resolutions") == ["0p50"]
        assert summary["grib"]["obtained"] == len(runner.settings.forecast_hours)
        assert summary["grib"]["cycle"]
        assert summary["metar"]["count"] == 1

    def test_initial_acquisition_tolerates_no_metar(self, isolated_db):
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (True, [])
        runner.metar.get_all_metars = lambda: None

        import asyncio

        summary = asyncio.run(runner.initial_acquisition())
        assert summary["grib"]["obtained"] == len(runner.settings.forecast_hours)
        assert "metar" in summary

    def test_initial_acquisition_tries_previous_cycle_when_latest_incomplete(self, isolated_db):
        """Se o ciclo publicado estiver incompleto, tenta o anterior."""
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        target = latest_published_cycle()
        prev = previous_cycle(*target)
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (ana == prev[1], [])
        runner.metar.get_all_metars = lambda: []

        import asyncio

        summary = asyncio.run(runner.initial_acquisition())
        assert len(fake.calls) >= 2, "deveria tentar o ciclo anterior"
        assert summary["grib"]["cycle"] == f"{prev[0]}_{prev[1]}"

    def test_initial_acquisition_no_complete_cycle_graceful(self, isolated_db):
        """Nenhum ciclo completo: servidor inicia mesmo assim (summary vazio)."""
        runner = SchedulerRunner()
        fake = FakeDownloader()
        runner.downloader = fake
        runner._cycle_has_complete_forecast = lambda date, ana, proc=None: (False, ["00"])
        runner.metar.get_all_metars = lambda: []

        import asyncio

        summary = asyncio.run(runner.initial_acquisition())
        assert summary["grib"]["cycle"] is None
        assert "metar" in summary

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


class TestGribDownloaderAtomic:
    """Download atômico: `.part` só vira arquivo final se o wget concluir."""

    def _paths(self):
        from server_MET.core.config import Settings

        dest = Settings().dir_gribs / "20260801" / "06"
        dest.mkdir(parents=True, exist_ok=True)
        return dest / "gfs.t06z.pgrb2.0p25.f000"

    def _fake_run(self, monkeypatch, *, exit_code=0, partial_first=True):
        from pathlib import Path

        from server_MET.acquisition.grib_downloader import GribDownloader

        d = GribDownloader()
        state = {"calls": 0}

        def fake_run(cmd, **kw):
            fp = cmd[2]
            state["calls"] += 1
            # sempre deixa o .part no disco (como o wget real faria)
            Path(fp).parent.mkdir(parents=True, exist_ok=True)
            Path(fp).write_bytes(b"conteudo")
            return type("R", (), {"returncode": exit_code, "stdout": b"", "stderr": b""})()

        monkeypatch.setattr("subprocess.run", fake_run)
        return d, state

    def test_download_success_renames_part(self, isolated_db, isolated_data_dirs, monkeypatch):
        from pathlib import Path

        d, state = self._fake_run(monkeypatch)
        fp = self._paths()
        ok = d.download_file("http://fake/gfs", fp)
        assert ok
        assert fp.exists(), "arquivo final deveria existir"
        part = Path(str(fp) + ".part")
        assert not part.exists(), ".part não deveria sobrar após sucesso"

    def test_download_failure_removes_part_and_keeps_no_final(self, isolated_db, isolated_data_dirs, monkeypatch):
        from pathlib import Path

        d, state = self._fake_run(monkeypatch, exit_code=1)
        fp = self._paths()
        ok = d.download_file("http://fake/gfs", fp)
        assert not ok
        assert not fp.exists(), "arquivo final não deveria existir após falha"
        part = Path(str(fp) + ".part")
        assert not part.exists(), ".part deveria ser limpo após falha"
