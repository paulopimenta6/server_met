"""Testes da camada de persistência SQLite."""
import json

from server_MET.persistence.database import Database, get_database, set_database
from server_MET.persistence.repositories import (
    AnalysisRepository,
    DownloadRepository,
    MetarRepository,
    OutputRepository,
    TaskRepository,
)


def _make_repos(db):
    return {
        "downloads": DownloadRepository(db),
        "outputs": OutputRepository(db),
        "metar": MetarRepository(db),
        "tasks": TaskRepository(db),
        "analysis": AnalysisRepository(db),
    }


class TestDatabase:
    def test_schema_idempotent(self, tmp_path):
        db = Database(tmp_path / "a.db")
        db.connect()
        db.create_schema()
        db.create_schema()
        counts = db.table_counts()
        assert set(counts) == {
            "downloads", "outputs", "metar_obs", "tasks", "analysis_results",
            "ingest_state", "grid_data",
        }
        assert db.user_version() == 2
        db.close()

    def test_wal_mode(self, tmp_path):
        db = Database(tmp_path / "wal.db")
        db.connect()
        row = db.fetchone("PRAGMA journal_mode")
        assert row["journal_mode"].lower() == "wal"
        db.close()

    def test_execute_params(self, tmp_path):
        db = Database(tmp_path / "p.db")
        db.connect()
        db.create_schema()
        db.execute("INSERT INTO tasks (id, task_type) VALUES (?, ?)", ("t1", "download"))
        row = db.fetchone("SELECT * FROM tasks WHERE id = ?", ("t1",))
        assert row["task_type"] == "download"
        db.close()


class TestDownloadRepository:
    def test_register_and_mark(self, isolated_db):
        repo = _make_repos(isolated_db)["downloads"]
        repo.register("20260101", "06", "0p25", "00", "/tmp/x.grb")
        repo.mark("20260101", "06", "0p25", "00", "downloaded", file_size=100)
        rows = repo.list(date_str="20260101")
        assert rows[0]["status"] == "downloaded"
        assert rows[0]["file_size"] == 100

    def test_invalid_status_raises(self, isolated_db):
        import pytest

        repo = _make_repos(isolated_db)["downloads"]
        with pytest.raises(ValueError):
            repo.mark("20260101", "06", "0p25", "00", "bogus")

    def test_register_idempotent(self, isolated_db):
        repo = _make_repos(isolated_db)["downloads"]
        repo.register("20260101", "06", "0p25", "00", "/a")
        repo.register("20260101", "06", "0p25", "00", "/b")
        assert repo.count() == 1


class TestOutputRepository:
    def test_register_and_list(self, isolated_db):
        repo = _make_repos(isolated_db)["outputs"]
        repo.register("map", "/data/map.png", variable="temp", region="SP",
                      date_str="20260101", analysis="06")
        rows = repo.list(kind="map", region="SP")
        assert len(rows) == 1
        assert rows[0]["variable"] == "temp"

    def test_invalid_kind_raises(self, isolated_db):
        import pytest

        repo = _make_repos(isolated_db)["outputs"]
        with pytest.raises(ValueError):
            repo.register("nope", "/x.png")


class TestMetarRepository:
    def test_upsert_keeps_history(self, isolated_db):
        repo = _make_repos(isolated_db)["metar"]
        repo.upsert("SBGR", "METAR SBGR 01", {"wind": {"speed": 5}}, {"temp": 15},
                    region="SP", obs_time="202601011200")
        repo.upsert("SBGR", "METAR SBGR 02", {"wind": {"speed": 7}}, {"temp": 16},
                    region="SP", obs_time="202601011800")
        rows = repo.list(icao="SBGR")
        assert len(rows) == 2
        parsed = json.loads(rows[-1]["parsed_json"])
        assert parsed["wind"]["speed"] == 7

    def test_upsert_same_obs_replaces(self, isolated_db):
        repo = _make_repos(isolated_db)["metar"]
        repo.upsert("SBGR", "A", {}, {}, obs_time="202601011200")
        repo.upsert("SBGR", "B", {}, {}, obs_time="202601011200")
        assert repo.count() == 1
        assert repo.list(icao="SBGR")[0]["raw_metar"] == "B"


class TestTaskRepository:
    def test_lifecycle(self, isolated_db):
        repo = _make_repos(isolated_db)["tasks"]
        task_id = repo.create("download", {"date": "20260101"})
        repo.update(task_id, status="running")
        repo.update(task_id, status="done", result={"count": 3})
        task = repo.get(task_id)
        assert task["status"] == "done"
        assert json.loads(task["result_json"])["count"] == 3
        assert task["task_type"] == "download"

    def test_get_missing(self, isolated_db):
        repo = _make_repos(isolated_db)["tasks"]
        assert repo.get("nao-existe") is None


class TestAnalysisRepository:
    def test_save_and_latest(self, isolated_db):
        repo = _make_repos(isolated_db)["analysis"]
        repo.save("summary", {"results": [1, 2]}, variable="temp", region="SP",
                  date_str="20260101", analysis="06")
        latest = repo.latest("summary", "temp", None, "SP", "20260101", "06")
        assert latest is not None
        assert latest["**cached**"] is True
        assert latest["results"] == [1, 2]

    def test_latest_none_when_missing(self, isolated_db):
        repo = _make_repos(isolated_db)["analysis"]
        assert repo.latest("summary", "temp", None, "SP", "20260101", "06") is None


class TestGetDatabase:
    def test_get_database_returns_shared(self, isolated_db):
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2
        assert db1.conn is not None
