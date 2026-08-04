#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maps endpoints - Server MET v2.0
Serve generated PNG maps
"""
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/maps", tags=["maps"])

MAPS_BASE_DIR = Path("/home/paulo/Documentos/meus_codigos/server_met/maps")

def _find_latest_map(variable: str, region: str, level: int = None, date: str = None, analysis: str = None, forecast: str = None):
    pattern_parts = ["GFS_*", region.upper(), f"N{level or '*'}", variable]
    if date:
        pattern_parts.append(date)
    if analysis:
        pattern_parts.append(analysis)
    if forecast:
        pattern_parts.append(forecast)
    
    pattern = "_".join(pattern_parts) + "*.png"
    
    matches = list(MAPS_BASE_DIR.rglob(pattern))
    if not matches:
        return None
    
    return max(matches, key=lambda p: p.stat().st_mtime)

@router.api_route("/{variable}/{region}", methods=["GET", "HEAD"])
async def get_map(
    request: Request,
    variable: str,
    region: str,
    level: int = None,
    date: str = None,
    analysis: str = None,
    forecast: str = None
):
    latest = _find_latest_map(variable, region, level, date, analysis, forecast)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No map found for {variable}/{region}")
    
    if request.method == "HEAD":
        return Response(media_type="image/png")
    
    return FileResponse(latest, media_type="image/png")

@router.get("/list/{variable}/{region}")
async def list_maps(variable: str, region: str):
    pattern = f"GFS_*_{region.upper()}_N*_{variable}*.png"
    matches = list(MAPS_BASE_DIR.rglob(pattern))
    
    maps = []
    for m in matches:
        rel_path = m.relative_to(MAPS_BASE_DIR)
        maps.append({
            "path": str(rel_path),
            "filename": m.name,
            "size": m.stat().st_size,
            "modified": m.stat().st_mtime
        })
    
    return {"maps": sorted(maps, key=lambda x: x["modified"], reverse=True)}