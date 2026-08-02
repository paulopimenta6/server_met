"""Fixtures compartilhadas: isolamento do banco SQLite e cliente HTTP."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Cada teste usa um banco SQLite descartável em tmp_path.

    Evita que os testes toquem em `data/met_server.db` e isola o cache
    de serviços da API entre execuções.
    """
    from server_MET.api import dependencies
    from server_MET.persistence.database import Database, set_database

    db = Database(tmp_path / "test_met.db")
    db.connect()
    db.create_schema()
    set_database(db)
    dependencies._services.clear()
    yield db
    db.close()


@pytest.fixture
def client():
    from server_MET.api.app import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
