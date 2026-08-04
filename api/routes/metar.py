#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
METAR endpoints - Server MET v2.0
Serve decoded METAR data persisted in SQLite.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from core.persistence import persistence

router = APIRouter(prefix="/metar", tags=["metar"])


@router.get("/stations")
async def list_stations():
    """List all available METAR stations."""
    stations = persistence.get_metar_stations()
    if not stations:
        # Fallback to the static registry so the UI always has options.
        from core.metar import DEFAULT_STATIONS
        stations = [
            {"code": code, "name": info["name"], "city": info["city"],
             "state": info["state"], "lat": None, "lon": None}
            for code, info in DEFAULT_STATIONS.items()
        ]
    return {"stations": stations}


@router.get("/{station_code}")
async def get_metar(
    station_code: str,
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    latest: bool = Query(True, description="Get latest available METAR"),
):
    """Get the latest (or dated) decoded METAR for a station."""
    station_code = station_code.upper()

    stations = persistence.get_metar_stations()
    if not any(s["code"] == station_code for s in stations):
        from core.metar import DEFAULT_STATIONS
        if station_code not in DEFAULT_STATIONS:
            raise HTTPException(status_code=404, detail=f"Station {station_code} not found")

    if latest:
        report = persistence.get_latest_metar(station_code)
        if not report:
            raise HTTPException(status_code=404, detail=f"No METAR data for station {station_code}")
        return {
            "station": station_code,
            "time": report["observed_at"],
            "metar": report["raw"],
            "decoded": report["decoded"],
            "temperature_c": report["temperature_c"],
            "dewpoint_c": report["dewpoint_c"],
            "wind_dir": report["wind_dir"],
            "wind_speed_kt": report["wind_speed_kt"],
            "visibility_km": report["visibility_km"],
            "altim_hpa": report["altim_hpa"],
            "flight_category": report["flight_category"],
        }

    # Historical path: read JSON snapshot files for a given date.
    from core.config import METAR_DIR
    import json
    station_dir = METAR_DIR / station_code
    if not station_dir.exists():
        raise HTTPException(status_code=404, detail=f"No METAR data for station {station_code}")
    files = list(station_dir.glob("*.json"))
    if date:
        files = [f for f in files if date in f.name]
    if not files:
        raise HTTPException(status_code=404, detail=f"No METAR for date {date}")
    metar_file = max(files, key=lambda p: p.stat().st_mtime)
    with open(metar_file, encoding="utf-8") as f:
        metar_data = json.load(f)
    return {
        "station": station_code,
        "time": metar_data.get("reportTime", ""),
        "metar": metar_data.get("rawOb", ""),
        "raw": metar_data.get("rawOb", ""),
    }


@router.get("/latest/all")
async def get_all_latest_metar():
    """Get the latest decoded METAR for all stations."""
    reports = persistence.get_all_latest_metar()
    return {
        "metars": [
            {
                "station": r["station_code"],
                "time": r["observed_at"],
                "metar": r["raw"],
                "decoded": r["decoded"],
                "flight_category": r["flight_category"],
            }
            for r in reports
        ]
    }