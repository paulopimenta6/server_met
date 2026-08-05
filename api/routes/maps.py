#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maps endpoints - Server MET v2.0
Serve generated PNG maps
"""
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import FileResponse
from pathlib import Path
import re
import os

from core.config import MAPS_DIR

router = APIRouter(prefix="/maps", tags=["maps"])

MAPS_BASE_DIR = MAPS_DIR

# Filenames produced by core.maps.generate_map:
#   GFS_<res>_<REGION>_N<level|SFC>_<variable>_<analysis>_<date>_<forecast>.png
# Variable codes may contain underscores (umidadeRel, total_o3, uSupe, ...).
_FILENAME_RE = re.compile(
    r"GFS_(?P<res>[^_]+)_(?P<region>[^_]+)_(?P<level>N\d+|NSFC)_"
    r"(?P<var>.+?)_(?P<ana>\d{2})_(?P<date>\d{8})_(?P<forecast>\d+)\.png"
)


def _find_latest_map(variable: str, region: str, level: int = None,
                     date: str = None, analysis: str = None,
                     forecast: str = None):
    region = region.upper()
    wanted_level = None if level is None else f"N{level}"
    matches = []
    for p in MAPS_BASE_DIR.rglob("GFS_*.png"):
        m = _FILENAME_RE.match(p.name)
        if not m:
            continue
        fields = m.groupdict()
        if fields["region"] != region or fields["var"] != variable:
            continue
        if wanted_level is not None and fields["level"] != wanted_level:
            continue
        if date and fields["date"] != date:
            continue
        if analysis and fields["ana"] != analysis:
            continue
        if forecast and int(fields["forecast"]) != int(forecast):
            continue
        matches.append(p)

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