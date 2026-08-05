#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data endpoints - Server MET v2.0
"""
from fastapi import APIRouter, Query, HTTPException, Response
from typing import List, Optional
from api.schemas import (
    DataQueryParams, DataListResponse, ProcessedDataResponse,
    VariableListResponse, VariableInfo, RegionListResponse, RegionInfo,
    StatsResponse
)
from core.persistence import persistence
from core.variables import VARIABLES_MET, get_all_variable_codes, get_variable_info, is_variable_available
from core.config import REGIOES
import os

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/variables", response_model=VariableListResponse)
async def list_variables():
    variables = []
    for code, info in VARIABLES_MET.items():
        variables.append(VariableInfo(
            code=code,
            name=info["grib_name"],
            level_type=info["level_type"],
            level_values=info.get("level_values", []),
            unit=info["unit"],
            description=info["description"],
            category=info["category"],
            available=is_variable_available(code)
        ))
    return VariableListResponse(variables=variables)

@router.get("/regions", response_model=RegionListResponse)
async def list_regions():
    regions = []
    for code, bounds in REGIOES.items():
        regions.append(RegionInfo(
            code=code,
            name=code,
            bounds=bounds
        ))
    return RegionListResponse(regions=regions)

@router.get("/", response_model=DataListResponse)
async def query_data(
    variable: Optional[str] = Query(None, description="Variable code (e.g., temp, o3, u)"),
    level: Optional[int] = Query(None, description="Pressure level in hPa or height in meters"),
    region: Optional[str] = Query(None, description="Region code (e.g., SP, RJ)"),
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    analysis: Optional[str] = Query(None, description="Analysis time (00, 06, 12, 18)"),
    forecast: Optional[int] = Query(None, description="Forecast hour (0, 6, 12, 18)"),
    limit: int = Query(100, ge=1, le=10000)
):
    data = persistence.query_data(
        variable_code=variable,
        level_value=level,
        region_code=region,
        data_date=date,
        analysis_time=analysis,
        forecast_hour=forecast,
        limit=limit
    )
    
    results = []
    for row in data:
        results.append(ProcessedDataResponse(
            id=row["id"],
            grib_metadata_id=row["grib_metadata_id"],
            variable_code=row["variable_code"],
            level_type=row["level_type"],
            level_value=row["level_value"],
            region_code=row["region_code"],
            min_value=row["min_value"],
            max_value=row["max_value"],
            mean_value=row["mean_value"],
            csv_path=row["csv_path"],
            created_at=row["created_at"],
            file_path=row.get("file_path"),
            analysis_time=row.get("analysis_time"),
            forecast_hour=row.get("forecast_hour"),
            data_date=row.get("data_date"),
            resolution=row.get("resolution")
        ))
    
    return DataListResponse(total=len(results), data=results)

@router.get("/latest", response_model=Optional[ProcessedDataResponse])
async def get_latest(
    variable: str = Query(..., description="Variable code"),
    region: str = Query(..., description="Region code"),
    level: int = Query(..., description="Level value")
):
    result = persistence.get_latest_data(variable, region, level)
    if not result:
        raise HTTPException(status_code=404, detail="No data found")
    
    return ProcessedDataResponse(
        id=result["id"],
        grib_metadata_id=result["grib_metadata_id"],
        variable_code=result["variable_code"],
        level_type=result["level_type"],
        level_value=result["level_value"],
        region_code=result["region_code"],
        min_value=result["min_value"],
        max_value=result["max_value"],
        mean_value=result["mean_value"],
        csv_path=result["csv_path"],
        created_at=result["created_at"],
        file_path=result.get("file_path"),
        analysis_time=result.get("analysis_time"),
        forecast_hour=result.get("forecast_hour"),
        data_date=result.get("data_date"),
        resolution=result.get("resolution")
    )

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    variable: str = Query(..., description="Variable code"),
    region: str = Query(..., description="Region code"),
    level: int = Query(..., description="Level value"),
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    analysis: Optional[str] = Query(None, description="Analysis time (00, 06, 12, 18)")
):
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
    return StatsResponse(
        variable=variable,
        level=level,
        region=region,
        date=row.get("data_date", ""),
        analysis=row.get("analysis_time", ""),
        min=row["min_value"] or 0,
        max=row["max_value"] or 0,
        mean=row["mean_value"] or 0,
        count=1
    )

@router.get("/available")
async def get_available():
    return {
        "variables": persistence.get_available_variables(),
        "regions": persistence.get_available_regions(),
        "dates": persistence.get_available_dates(),
        "analyses": persistence.get_available_analyses(),
        "forecasts": persistence.get_available_forecasts()
    }

@router.get("/dashboard")
async def get_dashboard():
    """Aggregate summary for the frontend statistical dashboard."""
    import sqlite3
    with persistence._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT variable_code), COUNT(DISTINCT region_code) FROM processed_data")
        total, nvars, nregs = cur.fetchone()
        cur.execute("SELECT variable_code, COUNT(*) n, AVG(mean_value) avg FROM processed_data GROUP BY variable_code ORDER BY variable_code")
        by_var = [{"variable": r[0], "records": r[1], "avg": round(r[2], 2)} for r in cur.fetchall()]
        cur.execute("SELECT region_code, COUNT(*) n FROM processed_data GROUP BY region_code ORDER BY region_code")
        by_region = [{"region": r[0], "records": r[1]} for r in cur.fetchall()]
        cur.execute("SELECT data_date, COUNT(*) n FROM grib_metadata GROUP BY data_date ORDER BY data_date DESC")
        by_date = [{"date": r[0], "records": r[1]} for r in cur.fetchall()]
        cur.execute("SELECT analysis_time, COUNT(*) n FROM grib_metadata GROUP BY analysis_time ORDER BY analysis_time")
        by_analysis = [{"analysis": r[0], "records": r[1]} for r in cur.fetchall()]
        cur.execute("SELECT forecast_hour, COUNT(*) n FROM grib_metadata GROUP BY forecast_hour ORDER BY forecast_hour")
        by_forecast = [{"forecast": r[0], "records": r[1]} for r in cur.fetchall()]

    metar_stats = persistence.get_metar_stats()
    return {
        "total_records": total or 0,
        "variables": nvars or 0,
        "regions": nregs or 0,
        "by_variable": by_var,
        "by_region": by_region,
        "by_date": by_date,
        "by_analysis": by_analysis,
        "by_forecast": by_forecast,
        "metar": metar_stats,
    }

@router.get("/levels/{variable}")
async def get_levels(variable: str):
    levels = persistence.get_available_levels(variable)
    return {"variable": variable, "levels": levels}

@router.get("/export/csv")
async def export_csv(
    variable: str = Query(...),
    region: str = Query(...),
    level: Optional[int] = Query(None, description="Level value; omit for surface variables"),
    date: Optional[str] = Query(None),
    analysis: Optional[str] = Query(None),
    forecast: Optional[int] = Query(None, description="Forecast hour (0, 6, 12, 18)")
):
    from pathlib import Path
    import tempfile
    
    level_value = level if level is not None else 0
    output_path = Path(tempfile.gettempdir()) / f"export_{variable}_{region}_{level_value}_{forecast or 0}.csv"
    count = persistence.export_csv(
        output_path, variable_code=variable, region_code=region,
        level_value=level_value, data_date=date, analysis_time=analysis,
        forecast_hour=forecast)
    
    if count == 0:
        raise HTTPException(status_code=404, detail="No data to export")
    
    return Response(
        content=output_path.read_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={output_path.name}"}
    )