#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch real METAR reports from the AviationWeather (NOAA) REST API
and persist them into SQLite (plus JSON snapshot files in data/metar).
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

import httpx

from core.config import AVIATION_WEATHER_URL, METAR_DIR
from core.persistence import persistence

logger = logging.getLogger(__name__)

DEFAULT_STATIONS = {
    "SBGR": {"name": "São Paulo/Guarulhos", "city": "São Paulo", "state": "SP"},
    "SBGL": {"name": "Rio de Janeiro/Galeão", "city": "Rio de Janeiro", "state": "RJ"},
    "SBBR": {"name": "Brasília", "city": "Brasília", "state": "DF"},
    "SBCF": {"name": "Belo Horizonte/Confins", "city": "Belo Horizonte", "state": "MG"},
    "SBPA": {"name": "Porto Alegre", "city": "Porto Alegre", "state": "RS"},
    "SBCT": {"name": "Curitiba", "city": "Curitiba", "state": "PR"},
    "SBBE": {"name": "Belém", "city": "Belém", "state": "PA"},
    "SBEG": {"name": "Manaus", "city": "Manaus", "state": "AM"},
    "SBRF": {"name": "Recife", "city": "Recife", "state": "PE"},
    "SBFZ": {"name": "Fortaleza", "city": "Fortaleza", "state": "CE"},
    "SBKP": {"name": "Campinas/Viracopos", "city": "Campinas", "state": "SP"},
    "SBFL": {"name": "Florianópolis", "city": "Florianópolis", "state": "SC"},
    "SBSV": {"name": "Salvador", "city": "Salvador", "state": "BA"},
    "SBGO": {"name": "Goiânia", "city": "Goiânia", "state": "GO"},
    "SBVT": {"name": "Vitória", "city": "Vitória", "state": "ES"},
}


def _iso_observed(report_time: str) -> str:
    """Normalize an ISO timestamp to a sortable string (YYYYMMDDHHMM)."""
    if report_time:
        try:
            return datetime.fromisoformat(report_time.replace("Z", "+00:00")).strftime("%Y%m%d%H%M")
        except Exception:
            pass
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")


def _decoded(report: Dict[str, Any]) -> str:
    """Build a human-readable decoded summary for a METAR record."""
    parts = []
    if report.get("temp") is not None:
        parts.append(f"Temperatura: {report['temp']}°C")
    if report.get("dewp") is not None:
        parts.append(f"Ponto de orvalho: {report['dewp']}°C")
    if report.get("wdir") is not None and report.get("wspd") is not None:
        parts.append(f"Vento: {report['wspd']}KT de direção {report['wdir']}°")
    if report.get("visib") is not None:
        parts.append(f"Visibilidade: {report['visib']} km")
    if report.get("altim") is not None:
        parts.append(f"Pressão (QNH): {report['altim']} hPa")
    if report.get("clouds"):
        skc = ", ".join(f"{c.get('cover','')} {c.get('base', '')}ft" for c in report["clouds"])
        parts.append(f"Nuvens: {skc}")
    elif report.get("cover"):
        parts.append(f"Cobertura: {report['cover']}")
    if report.get("fltCat"):
        parts.append(f"Classificação: {report['fltCat']}")
    return "\n".join(parts) if parts else "Dados parciais disponíveis."


def fetch_metar(stations: Optional[List[str]] = None,
                ids: Optional[str] = None,
                timeout: int = 20) -> List[Dict[str, Any]]:
    """Download live METAR reports for one or many ICAO stations."""
    if ids is None:
        ids = ",".join(stations or list(DEFAULT_STATIONS.keys()))
    url = f"{AVIATION_WEATHER_URL}?ids={ids}&format=json"
    logger.info("Fetching METAR from %s", url)
    resp = httpx.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _persist_report(item: Dict[str, Any]) -> Dict[str, Any]:
    code = item["icaoId"]
    report = {
        "station_code": code,
        "observed_at": _iso_observed(item.get("reportTime")),
        "raw": item.get("rawOb", ""),
        "decoded": _decoded(item),
        "temperature_c": item.get("temp"),
        "dewpoint_c": item.get("dewp"),
        "wind_dir": item.get("wdir"),
        "wind_speed_kt": item.get("wspd"),
        "visibility_km": item.get("visib"),
        "altim_hpa": item.get("altim"),
        "cloud_skc": item.get("cover") or "",
        "flight_category": item.get("fltCat") or "",
    }
    station_dir = METAR_DIR / code
    station_dir.mkdir(parents=True, exist_ok=True)
    snapshot = station_dir / f"{code}{report['observed_at']}.json"
    snapshot.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")

    persistence.upsert_station(
        code=code,
        name=item.get("name") or DEFAULT_STATIONS.get(code, {}).get("name"),
        city=DEFAULT_STATIONS.get(code, {}).get("city"),
        state=DEFAULT_STATIONS.get(code, {}).get("state"),
        lat=item.get("lat"), lon=item.get("lon"),
    )
    persistence.save_metar_report(report)
    return report


def fetch_and_store(stations: Optional[List[str]] = None) -> Dict[str, Any]:
    """Download, decode and persist live METAR data for all stations."""
    items = fetch_metar(stations=stations)
    saved = [_persist_report(it) for it in items if it.get("icaoId")]
    logger.info("Persisted %d METAR reports", len(saved))
    stats = persistence.get_metar_stats()
    stats["saved"] = len(saved)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_and_store())