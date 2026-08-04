#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camada de persistência: SQLite + CSV para Server MET v2.0
"""
import sqlite3
import csv
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging

from core.config import SQLITE_DB_PATH, CSV_EXPORT_DIR

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS grib_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    analysis_time TEXT NOT NULL,
    forecast_hour INTEGER NOT NULL,
    data_date TEXT NOT NULL,
    resolution TEXT NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grib_metadata_id INTEGER NOT NULL,
    variable_code TEXT NOT NULL,
    level_type TEXT NOT NULL,
    level_value INTEGER NOT NULL,
    region_code TEXT NOT NULL,
    min_value REAL,
    max_value REAL,
    mean_value REAL,
    data_json TEXT,
    csv_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grib_metadata_id) REFERENCES grib_metadata(id)
);

CREATE INDEX IF NOT EXISTS idx_grib_lookup ON grib_metadata(data_date, analysis_time, forecast_hour, resolution);
CREATE INDEX IF NOT EXISTS idx_processed_lookup ON processed_data(variable_code, level_value, region_code);
CREATE INDEX IF NOT EXISTS idx_processed_grib ON processed_data(grib_metadata_id);

CREATE TABLE IF NOT EXISTS metar_stations (
    code TEXT PRIMARY KEY,
    name TEXT,
    city TEXT,
    state TEXT,
    lat REAL,
    lon REAL
);

CREATE TABLE IF NOT EXISTS metar_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    raw TEXT NOT NULL,
    decoded TEXT,
    temperature_c REAL,
    dewpoint_c REAL,
    wind_dir INTEGER,
    wind_speed_kt INTEGER,
    visibility_km REAL,
    altim_hpa REAL,
    cloud_skc TEXT,
    flight_category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(station_code, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_metar_station_time ON metar_reports(station_code, observed_at);
"""

class PersistenceManager:
    def __init__(self, db_path: Path = SQLITE_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_grib_metadata(
        self,
        file_path: str,
        analysis_time: str,
        forecast_hour: int,
        data_date: str,
        resolution: str
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO grib_metadata 
                (file_path, analysis_time, forecast_hour, data_date, resolution)
                VALUES (?, ?, ?, ?, ?)
            """, (file_path, analysis_time, forecast_hour, data_date, resolution))
            conn.commit()
            cursor.execute("SELECT id FROM grib_metadata WHERE file_path = ?", (file_path,))
            row = cursor.fetchone()
            return row[0] if row else cursor.lastrowid
    
    def save_processed_data(
        self,
        grib_metadata_id: int,
        variable_code: str,
        level_type: str,
        level_value: int,
        region_code: str,
        min_value: float,
        max_value: float,
        mean_value: float,
        data_matrix: List[List[float]],
        lats: List[float],
        lons: List[float]
    ) -> int:
        csv_filename = f"{variable_code}_{level_type}_{level_value}_{region_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = CSV_EXPORT_DIR / csv_filename
        CSV_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        self._write_csv(csv_path, data_matrix, lats, lons, variable_code)
        
        data_json = json.dumps({
            "matrix": data_matrix,
            "lats": lats,
            "lons": lons
        })
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processed_data 
                (grib_metadata_id, variable_code, level_type, level_value, region_code,
                 min_value, max_value, mean_value, data_json, csv_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (grib_metadata_id, variable_code, level_type, level_value, region_code,
                  min_value, max_value, mean_value, data_json, str(csv_path)))
            conn.commit()
            return cursor.lastrowid
    
    def _write_csv(self, csv_path: Path, matrix: List[List[float]], lats: List[float], lons: List[float], var_name: str):
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["lat", "lon", var_name])
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    if i < len(matrix) and j < len(matrix[i]):
                        writer.writerow([lat, lon, matrix[i][j]])
    
    def query_data(
        self,
        variable_code: Optional[str] = None,
        level_value: Optional[int] = None,
        region_code: Optional[str] = None,
        data_date: Optional[str] = None,
        analysis_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT pd.*, gm.file_path, gm.analysis_time, gm.forecast_hour, gm.data_date, gm.resolution
            FROM processed_data pd
            JOIN grib_metadata gm ON pd.grib_metadata_id = gm.id
            WHERE 1=1
        """
        params = []
        
        if variable_code:
            query += " AND pd.variable_code = ?"
            params.append(variable_code)
        if level_value is not None:
            query += " AND pd.level_value = ?"
            params.append(level_value)
        if region_code:
            query += " AND pd.region_code = ?"
            params.append(region_code)
        if data_date:
            query += " AND gm.data_date = ?"
            params.append(data_date)
        if analysis_time:
            query += " AND gm.analysis_time = ?"
            params.append(analysis_time)
        
        query += " ORDER BY gm.data_date DESC, gm.analysis_time DESC, gm.forecast_hour DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_data(self, variable_code: str, region_code: str, level_value: int) -> Optional[Dict[str, Any]]:
        results = self.query_data(variable_code, level_value, region_code, limit=1)
        return results[0] if results else None
    
    def export_csv(self, output_path: Path, **filters) -> int:
        data = self.query_data(**filters, limit=10000)
        if not data:
            return 0
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        return len(data)
    
    def get_available_variables(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT variable_code FROM processed_data ORDER BY variable_code")
            return [row[0] for row in cursor.fetchall()]
    
    def get_available_regions(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT region_code FROM processed_data ORDER BY region_code")
            return [row[0] for row in cursor.fetchall()]
    
    def get_available_levels(self, variable_code: str) -> List[int]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT level_value FROM processed_data WHERE variable_code = ? ORDER BY level_value",
                (variable_code,)
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_available_dates(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT data_date FROM grib_metadata ORDER BY data_date DESC")
            return [row[0] for row in cursor.fetchall()]

    # ------------------------------------------------------------------ #
    # METAR persistence
    # ------------------------------------------------------------------ #
    def upsert_station(self, code: str, name: str = None, city: str = None,
                       state: str = None, lat: float = None, lon: float = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metar_stations (code, name, city, state, lat, lon)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    name=excluded.name, city=excluded.city, state=excluded.state,
                    lat=excluded.lat, lon=excluded.lon
            """, (code, name, city, state, lat, lon))
            conn.commit()
            return cursor.lastrowid

    def save_metar_report(self, report: Dict[str, Any]) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metar_reports
                (station_code, observed_at, raw, decoded, temperature_c, dewpoint_c,
                 wind_dir, wind_speed_kt, visibility_km, altim_hpa, cloud_skc, flight_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(station_code, observed_at) DO UPDATE SET
                    raw=excluded.raw, decoded=excluded.decoded,
                    temperature_c=excluded.temperature_c, dewpoint_c=excluded.dewpoint_c,
                    wind_dir=excluded.wind_dir, wind_speed_kt=excluded.wind_speed_kt,
                    visibility_km=excluded.visibility_km, altim_hpa=excluded.altim_hpa,
                    cloud_skc=excluded.cloud_skc, flight_category=excluded.flight_category
            """, (
                report["station_code"], report["observed_at"], report["raw"], report.get("decoded"),
                report.get("temperature_c"), report.get("dewpoint_c"), report.get("wind_dir"),
                report.get("wind_speed_kt"), report.get("visibility_km"), report.get("altim_hpa"),
                report.get("cloud_skc"), report.get("flight_category")
            ))
            conn.commit()
            return cursor.lastrowid

    def get_latest_metar(self, station_code: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM metar_reports WHERE station_code = ? ORDER BY observed_at DESC LIMIT 1",
                (station_code,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_metar_stations(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM metar_stations ORDER BY code")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_latest_metar(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT r.* FROM metar_reports r
                JOIN (SELECT station_code, MAX(observed_at) max_t FROM metar_reports
                      GROUP BY station_code) latest
                ON r.station_code = latest.station_code AND r.observed_at = latest.max_t
                ORDER BY r.station_code
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_metar_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            stations = self.get_metar_stations()
            reports = conn.execute("SELECT COUNT(*) total, COUNT(DISTINCT station_code) stations FROM metar_reports").fetchone()
            latest = conn.execute("SELECT MAX(observed_at) latest FROM metar_reports").fetchone()
            return {
                "stations": len(stations),
                "reports": reports["total"] if reports else 0,
                "stations_with_data": reports["stations"] if reports else 0,
                "latest_observation": latest["latest"] if latest else None,
            }

persistence = PersistenceManager()