"""Gerenciamento da conexão SQLite.

- Conexão única por processo (`Database`), com `check_same_thread=False` e lock
  para acesso seguro a partir de threads (background tasks do FastAPI).
- WAL mode + `busy_timeout` para leitura/escrita concorrente.
- `create_schema()` idempotente; migrações via `PRAGMA user_version`.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional, Sequence

from server_MET.core.config import Settings
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.schemas import INDEXES_DDL, SCHEMA_VERSION, TABLES_DDL

logger = get_logger(__name__)

_default: Optional["Database"] = None


def get_database() -> "Database":
    """Retorna a instância padrão do banco (conectada e com schema criado)."""
    global _default
    if _default is None:
        _default = Database()
    if _default.conn is None:
        _default.connect()
    _default.create_schema()
    return _default


def set_database(db: "Database") -> None:
    """Define o banco padrão (usado em testes para isolar com tmp_path)."""
    global _default
    _default = db


class Database:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else Settings().db_path
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        return self._conn

    def connect(self) -> "Database":
        if self._conn is not None:
            return self
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        with conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
        self._conn = conn
        logger.info("Banco SQLite conectado: %s", self.db_path)
        return self

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def create_schema(self) -> None:
        if self._conn is None:
            self.connect()
        with self._lock, self._conn:
            for ddl in TABLES_DDL:
                self._conn.execute(ddl)
            for idx in INDEXES_DDL:
                self._conn.execute(idx)
        version = self.user_version()
        if version < SCHEMA_VERSION:
            self.set_user_version(SCHEMA_VERSION)
            logger.info("Schema SQLite inicializado (user_version=%s)", SCHEMA_VERSION)

    def migrate(self) -> None:
        """Ponto de extensão para migrações futuras (versão > atual)."""
        self.create_schema()

    def user_version(self) -> int:
        with self._lock:
            row = self.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row else 0

    def set_user_version(self, version: int) -> None:
        self.execute(f"PRAGMA user_version = {int(version)}")

    def execute(
        self, sql: str, params: Sequence[Any] = ()
    ) -> sqlite3.Cursor:
        if self._conn is None:
            self.connect()
        with self._lock, self._conn:
            return self._conn.execute(sql, params)

    def executemany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> None:
        if self._conn is None:
            self.connect()
        with self._lock, self._conn:
            self._conn.executemany(sql, seq_of_params)

    def fetchall(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        cur = self.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def fetchone(self, sql: str, params: Sequence[Any] = ()) -> Optional[dict]:
        cur = self.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def table_counts(self) -> dict[str, int]:
        tables = [
            row["name"]
            for row in self.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        counts = {}
        for t in tables:
            row = self.fetchone(f"SELECT COUNT(*) AS n FROM {t}")
            counts[t] = int(row["n"]) if row else 0
        return counts


__all__ = ["Database", "get_database", "set_database"]
