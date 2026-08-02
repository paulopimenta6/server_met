"""DDL (esquema) do banco de dados SQLite do servidor meteorológico."""
from __future__ import annotations

SCHEMA_VERSION = 2

TABLES_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_str TEXT NOT NULL,
        analysis_hour TEXT NOT NULL,
        resolution TEXT NOT NULL,
        forecast_hour TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        status TEXT NOT NULL DEFAULT 'pending',
        error TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (date_str, analysis_hour, resolution, forecast_hour)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        variable TEXT,
        level INTEGER,
        region TEXT,
        date_str TEXT,
        analysis TEXT,
        forecast TEXT,
        file_path TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS metar_obs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icao TEXT NOT NULL,
        region TEXT,
        raw_metar TEXT,
        parsed_json TEXT,
        metadata_json TEXT,
        obs_time TEXT,
        fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (icao, obs_time)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        task_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        payload_json TEXT,
        result_json TEXT,
        error TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        variable TEXT,
        level INTEGER,
        region TEXT,
        date_str TEXT,
        analysis TEXT,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ingest_state (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS grid_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        variable TEXT NOT NULL,
        level INTEGER,
        region TEXT NOT NULL,
        date_str TEXT NOT NULL,
        analysis TEXT NOT NULL,
        forecast INTEGER,
        resolution TEXT,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        value REAL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
]

INDEXES_DDL: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads (date_str, analysis_hour)",
    "CREATE INDEX IF NOT EXISTS idx_outputs_kind ON outputs (kind, region, date_str)",
    "CREATE INDEX IF NOT EXISTS idx_metar_icao ON metar_obs (icao)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_lookup ON analysis_results (kind, region, date_str, variable)",
    "CREATE INDEX IF NOT EXISTS idx_grid_lookup ON grid_data (variable, region, date_str, analysis, forecast)",
]

__all__ = ["SCHEMA_VERSION", "TABLES_DDL", "INDEXES_DDL"]
