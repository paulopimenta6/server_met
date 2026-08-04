#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maps endpoints - Server MET v2.0
Serve generated PNG maps
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/maps", tags=["maps"])

MAPS_BASE_DIR = Path("/home/paulo/Documentos/meus_codigos/server_met/maps")

@router.get("/{variable}/{region}")
async def get_map(
    variable: str,
    region: str,
    level: int = None,
    date: str = None,
    analysis: str = None,
    forecast: str = None
):
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
        raise HTTPException(status_code=404, detail=f"No map found for {variable}/{region}")
    
    latest = max(matches, key=lambda p: p.stat().st_mtime)
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

@router.get("/geojson/{variable}/{region}")
async def get_geojson(
    variable: str,
    region: str,
    level: int = None,
    date: str = None,
    analysis: str = None
):
    # Return data as GeoJSON for frontend mapping
    from core.persistence import persistence
    
    data = persistence.query_data(
        variable_code=variable,
        level_value=level,
        region_code=region,
        data_date=date,
        analysis_time=analysis,
        limit=1
    )
    
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    
    row = data[0]
    import json
    geojson_data = json.loads(row["data_json"]) if row["data_json"] else None
    
    if not geojson_data:
        raise HTTPException(status_code=404, detail="No matrix data available")
    
    matrix = geojson_data["matrix"]
    lats = geojson_data["lats"]
    lons = geojson_data["lons"]
    
    features = []
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            if i < len(matrix) and j < len(matrix[i]):
                value = matrix[i][j]
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "value": value,
                        "variable": variable,
                        "level": level,
                        "region": region
                    }
                })
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "bbox": [min(lons), min(lats), max(lons), max(lats)]
    }