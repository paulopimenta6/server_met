"""Repositórios (CRUD tipado) para as tabelas do banco SQLite.

Todos os SQL usam parâmetros vinculados — nunca f-strings.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from server_MET.core.logging_conf import get_logger
from server_MET.persistence.database import Database, get_database

logger = get_logger(__name__)

DOWNLOAD_STATUSES = ("pending", "downloaded", "skipped", "failed")
TASK_STATUSES = ("pending", "running", "done", "failed")
OUTPUT_KINDS = ("map", "matrix", "bluesky", "chart", "gif")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DownloadRepository:
    """Histórico de downloads de arquivos GRIB."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def register(
        self,
        date_str: str,
        analysis_hour: str,
        resolution: str,
        forecast_hour: str,
        file_path: str,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO downloads (date_str, analysis_hour, resolution, forecast_hour, file_path, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            ON CONFLICT (date_str, analysis_hour, resolution, forecast_hour)
            DO UPDATE SET file_path = excluded.file_path,
                          status = CASE
                              WHEN downloads.status = 'downloaded' THEN downloads.status
                              ELSE 'pending'
                          END,
                          updated_at = datetime('now')
            """,
            (date_str, analysis_hour, resolution, forecast_hour, str(file_path)),
        )

    def mark(
        self,
        date_str: str,
        analysis_hour: str,
        resolution: str,
        forecast_hour: str,
        status: str,
        file_size: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        if status not in DOWNLOAD_STATUSES:
            raise ValueError(f"Status inválido: {status}")
        self.db.execute(
            """
            UPDATE downloads
            SET status = ?, file_size = COALESCE(?, file_size),
                error = ?, updated_at = datetime('now')
            WHERE date_str = ? AND analysis_hour = ? AND resolution = ? AND forecast_hour = ?
            """,
            (status, file_size, error, date_str, analysis_hour, resolution, forecast_hour),
        )

    def list(
        self,
        date_str: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        sql = "SELECT * FROM downloads WHERE 1=1"
        params: list[Any] = []
        if date_str:
            sql += " AND date_str = ?"
            params.append(date_str)
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM downloads")
        return int(row["n"]) if row else 0


class OutputRepository:
    """Registro de artefatos gerados (mapas, matrizes, charts)."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def register(
        self,
        kind: str,
        file_path: str,
        variable: Optional[str] = None,
        level: Optional[int] = None,
        region: Optional[str] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        forecast: Optional[str] = None,
    ) -> None:
        if kind not in OUTPUT_KINDS:
            raise ValueError(f"Kind inválido: {kind}")
        self.db.execute(
            """
            INSERT INTO outputs (kind, variable, level, region, date_str, analysis, forecast, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (kind, variable, level, region, date_str, analysis, forecast, str(file_path)),
        )

    def list(
        self,
        kind: Optional[str] = None,
        region: Optional[str] = None,
        date_str: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        sql = "SELECT * FROM outputs WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if region:
            sql += " AND region = ?"
            params.append(region)
        if date_str:
            sql += " AND date_str = ?"
            params.append(date_str)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM outputs")
        return int(row["n"]) if row else 0


class MetarRepository:
    """Arquivo histórico de observações METAR."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def upsert(
        self,
        icao: str,
        raw_metar: str,
        parsed: Optional[dict] = None,
        metadata: Optional[dict] = None,
        region: Optional[str] = None,
        obs_time: Optional[str] = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO metar_obs (icao, region, raw_metar, parsed_json, metadata_json, obs_time, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (icao, obs_time) DO UPDATE SET
                raw_metar = excluded.raw_metar,
                parsed_json = excluded.parsed_json,
                metadata_json = excluded.metadata_json,
                fetched_at = excluded.fetched_at
            """,
            (
                icao,
                region,
                raw_metar,
                json.dumps(parsed, ensure_ascii=False) if parsed else None,
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
                obs_time or _now(),
                _now(),
            ),
        )

    def list(self, icao: Optional[str] = None, limit: int = 200) -> list[dict]:
        sql = "SELECT * FROM metar_obs WHERE 1=1"
        params: list[Any] = []
        if icao:
            sql += " AND icao = ?"
            params.append(icao)
        sql += " ORDER BY fetched_at DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM metar_obs")
        return int(row["n"]) if row else 0


class TaskRepository:
    """Registro persistente de tarefas em background (sobrevive a restart)."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def create(self, task_type: str, payload: Optional[dict] = None) -> str:
        task_id = uuid.uuid4().hex
        self.db.execute(
            "INSERT INTO tasks (id, task_type, status, payload_json) VALUES (?, ?, 'pending', ?)",
            (task_id, task_type, json.dumps(payload, ensure_ascii=False) if payload else None),
        )
        return task_id

    def update(
        self,
        task_id: str,
        status: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        if status is not None and status not in TASK_STATUSES:
            raise ValueError(f"Status inválido: {status}")
        sets = ["updated_at = datetime('now')"]
        params: list[Any] = []
        if status is not None:
            sets.append("status = ?")
            params.append(status)
        if result is not None:
            sets.append("result_json = ?")
            params.append(json.dumps(result, ensure_ascii=False))
        if error is not None:
            sets.append("error = ?")
            params.append(error)
        params.append(task_id)
        self.db.execute(
            f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", params
        )

    def get(self, task_id: str) -> Optional[dict]:
        return self.db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))

    def list(self, limit: int = 50) -> list[dict]:
        return self.db.fetchall("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM tasks")
        return int(row["n"]) if row else 0


class AnalysisRepository:
    """Resultados de análise persistidos (permite re-servir sem recomputar)."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def save(
        self,
        kind: str,
        result: dict,
        variable: Optional[str] = None,
        level: Optional[int] = None,
        region: Optional[str] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> None:
        self.db.execute(
            """
            DELETE FROM analysis_results
            WHERE kind = ? AND variable IS ? AND level IS ? AND region IS ? AND date_str IS ?
            """,
            (kind, variable, level, region, date_str),
        )
        self.db.execute(
            """
            INSERT INTO analysis_results (kind, variable, level, region, date_str, analysis, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kind,
                variable,
                level,
                region,
                date_str,
                analysis,
                json.dumps(result, ensure_ascii=False, default=str),
            ),
        )

    def latest(
        self,
        kind: str,
        variable: Optional[str] = None,
        level: Optional[int] = None,
        region: Optional[str] = None,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> Optional[dict]:
        sql = "SELECT * FROM analysis_results WHERE kind = ?"
        params: list[Any] = [kind]
        if variable:
            sql += " AND variable = ?"
            params.append(variable)
        if level:
            sql += " AND level = ?"
            params.append(level)
        if region:
            sql += " AND region = ?"
            params.append(region)
        if date_str:
            sql += " AND date_str = ?"
            params.append(date_str)
        if analysis:
            sql += " AND analysis = ?"
            params.append(analysis)
        sql += " ORDER BY id DESC LIMIT 1"
        row = self.db.fetchone(sql, params)
        if not row:
            return None
        result = json.loads(row["result_json"])
        return {"**cached**": True, **result}

    def list(
        self,
        kind: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        sql = "SELECT * FROM analysis_results WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if region:
            sql += " AND region = ?"
            params.append(region)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM analysis_results")
        return int(row["n"]) if row else 0


class GridDataRepository:
    """Dados de grade (matrizes) persistidos também no SQLite.

    Complementa os arquivos CSV (persistência dupla): cada ponto da matriz
    é inserido como uma linha, permitindo consultas programáticas sem
    depender de arquivos.
    """

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def save_region(
        self,
        variable: str,
        region: str,
        date_str: str,
        analysis: str,
        forecast: Optional[int],
        resolution: Optional[str],
        level: Optional[int],
        lat: Any,
        lon: Any,
        values: Any,
    ) -> int:
        """Insere a grade de uma região/variável/forecast num único commit."""
        lat_arr = list(lat)
        lon_arr = list(lon)
        val_flat = np.ravel(np.asarray(values, dtype=float))
        rows = []
        for j in range(len(lat_arr)):
            for i in range(len(lon_arr)):
                idx = j * len(lon_arr) + i
                v = float(val_flat[idx]) if idx < val_flat.size else None
                rows.append(
                    (
                        variable, level, region, date_str, analysis,
                        forecast, resolution, float(lat_arr[j]), float(lon_arr[i]), v,
                    )
                )
        self.db.executemany(
            """
            INSERT INTO grid_data
                (variable, level, region, date_str, analysis, forecast, resolution,
                 lat, lon, value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return len(rows)

    def delete_region(
        self,
        variable: str,
        region: str,
        date_str: str,
        analysis: str,
        forecast: Optional[int] = None,
        level: Optional[int] = None,
    ) -> int:
        sql = (
            "DELETE FROM grid_data WHERE variable = ? AND region = ? "
            "AND date_str = ? AND analysis = ?"
        )
        params: list[Any] = [variable, region, date_str, analysis]
        if forecast is not None:
            sql += " AND forecast = ?"
            params.append(forecast)
        if level is not None:
            sql += " AND level = ?"
            params.append(level)
        cur = self.db.execute(sql, params)
        return cur.rowcount if cur else 0

    def query(
        self,
        variable: str,
        region: str,
        date_str: str,
        analysis: str,
        forecast: Optional[int] = None,
        level: Optional[int] = None,
        limit: int = 100000,
    ) -> list[dict]:
        sql = (
            "SELECT variable, level, region, date_str, analysis, forecast, "
            "resolution, lat, lon, value FROM grid_data "
            "WHERE variable = ? AND region = ? AND date_str = ? AND analysis = ?"
        )
        params: list[Any] = [variable, region, date_str, analysis]
        if forecast is not None:
            sql += " AND forecast = ?"
            params.append(forecast)
        if level is not None:
            sql += " AND level = ?"
            params.append(level)
        sql += " ORDER BY lat DESC, lon ASC LIMIT ?"
        params.append(limit)
        return self.db.fetchall(sql, params)

    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS n FROM grid_data")
        return int(row["n"]) if row else 0


class IngestStateRepository:
    """Estado da captação contínua (chave/valor persistido no SQLite)."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_database()

    def get(self, key: str) -> Optional[str]:
        row = self.db.fetchone(
            "SELECT value FROM ingest_state WHERE key = ?", (key,)
        )
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        self.db.execute(
            """
            INSERT INTO ingest_state (key, value) VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value,
                                            updated_at = datetime('now')
            """,
            (key, value),
        )

    def get_json(self, key: str, default=None):
        raw = self.get(key)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    def set_json(self, key: str, value) -> None:
        self.set(key, json.dumps(value, ensure_ascii=False, default=str))

    def all(self) -> dict[str, str]:
        rows = self.db.fetchall("SELECT key, value FROM ingest_state")
        return {r["key"]: r["value"] for r in rows}


__all__ = [
    "DownloadRepository",
    "OutputRepository",
    "MetarRepository",
    "TaskRepository",
    "AnalysisRepository",
    "GridDataRepository",
    "IngestStateRepository",
]
