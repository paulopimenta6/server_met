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


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    """Redireciona todos os diretórios de dados do `Settings` para `tmp_path`.

    Evita que os testes criem datas/arquivos falsos no `data/` real
    (gribs, mapas, matrizes, análises e tmp).
    """
    from server_MET.core.config import Settings

    def _make_dir(name: str):
        def _property(self):
            return tmp_path / name

        return property(_property)

    for attr, subdir in {
        "dir_gribs": "gribs",
        "dir_mapas": "mapas",
        "dir_matrizes": "matrizes",
        "dir_matrizes_bluesky": "matrizes/bluesky",
        "dir_analise": "analise",
        "dir_tmp": "tmp",
    }.items():
        monkeypatch.setattr(Settings, attr, _make_dir(subdir))
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def client():
    from server_MET.api.app import app

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
