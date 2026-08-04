#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
METAR endpoints - Server MET v2.0
Serve METAR data from aviation weather stations
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json
from pathlib import Path

router = APIRouter(prefix="/metar", tags=["metar"])

METAR_DATA_DIR = Path("/home/paulo/Documentos/meus_codigos/server_met/data/metar")
METAR_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Brazilian aviation stations
STATIONS = {
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

@router.get("/stations")
async def list_stations():
    """List all available METAR stations"""
    stations_list = []
    for code, info in STATIONS.items():
        stations_list.append({
            "code": code,
            "name": info["name"],
            "city": info["city"],
            "state": info["state"]
        })
    return {"stations": stations_list}

@router.get("/{station_code}")
async def get_metar(
    station_code: str,
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    latest: bool = Query(True, description="Get latest available METAR")
):
    """Get METAR for a specific station"""
    station_code = station_code.upper()
    
    if station_code not in STATIONS:
        raise HTTPException(status_code=404, detail=f"Station {station_code} not found")
    
    # Look for METAR files in data/metar/{station_code}/
    station_dir = METAR_DATA_DIR / station_code
    if not station_dir.exists():
        raise HTTPException(status_code=404, detail=f"No METAR data for station {station_code}")
    
    # Find METAR files
    metar_files = list(station_dir.glob("*.json"))
    if not metar_files:
        raise HTTPException(status_code=404, detail=f"No METAR files for station {station_code}")
    
    if date:
        # Filter by date
        metar_files = [f for f in metar_files if date in f.name]
    
    if not metar_files:
        raise HTTPException(status_code=404, detail=f"No METAR for date {date}")
    
    # Get latest or specific file
    metar_file = max(metar_files, key=lambda p: p.stat().st_mtime)
    
    with open(metar_file) as f:
        metar_data = json.load(f)
    
    return {
        "station": station_code,
        "station_info": STATIONS[station_code],
        "time": metar_data.get("time", ""),
        "metar": metar_data.get("metar", ""),
        "raw": metar_data.get("raw", "")
    }

@router.get("/latest/all")
async def get_all_latest_metar():
    """Get latest METAR for all stations"""
    results = []
    for code in STATIONS.keys():
        station_dir = METAR_DATA_DIR / code
        if station_dir.exists():
            metar_files = list(station_dir.glob("*.json"))
            if metar_files:
                latest_file = max(metar_files, key=lambda p: p.stat().st_mtime)
                with open(latest_file) as f:
                    metar_data = json.load(f)
                results.append({
                    "station": code,
                    "station_info": STATIONS[code],
                    "time": metar_data.get("time", ""),
                    "metar": metar_data.get("metar", "")
                })
    return {"metars": results}