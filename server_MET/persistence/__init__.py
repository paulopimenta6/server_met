"""Camada de persistência em SQLite.

Tabelas: downloads, outputs, metar_obs, tasks e analysis_results.
Banco padrão: `data/met_server.db` (configurável via `db_file` em path.conf).
"""
from __future__ import annotations

from server_MET.persistence.database import Database, get_database
from server_MET.persistence.repositories import (
    AnalysisRepository,
    DownloadRepository,
    MetarRepository,
    OutputRepository,
    TaskRepository,
)

__all__ = [
    "Database",
    "get_database",
    "AnalysisRepository",
    "DownloadRepository",
    "MetarRepository",
    "OutputRepository",
    "TaskRepository",
]
