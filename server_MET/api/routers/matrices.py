"""Rotas de geração de matrizes CSV e matrizes BlueSky."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server_MET.api.dependencies import (
    build_region,
    get_grid_repo,
    get_matrix_generator,
    get_settings,
)
from server_MET.core.config import Settings
from server_MET.core.models import GribRequest, WindRequest
from server_MET.persistence.repositories import GridDataRepository

router = APIRouter(tags=["matrices"])


@router.post("/matrices/generate")
async def generate_matrix(
    request: GribRequest,
    settings: Settings = Depends(get_settings),
    matrix_generator=Depends(get_matrix_generator),
):
    region = build_region(request)
    date_str = request.date or matrix_generator.processor.get_date_str()
    ana = request.analysis or matrix_generator.processor.get_current_analysis_hour()
    output_dir = str(settings.dir_tmp / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    fhs = [request.forecast] if request.forecast else None
    files = matrix_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        forecast_hours=fhs,
        output_dir=output_dir,
    )
    if not files:
        raise HTTPException(status_code=500, detail="Falha na geração de matrizes")
    return {"matrices": files, "count": len(files)}


@router.post("/bluesky/wind")
async def generate_bluesky_wind(
    request: WindRequest,
    matrix_generator=Depends(get_matrix_generator),
):
    region = build_region(request)
    result = matrix_generator.generate_bluesky(
        region=region,
        level=request.level,
        date_str=request.date,
        analysis=request.analysis,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Falha na geração da matriz BlueSky")
    return {"file": result}


@router.get("/matrices/data")
async def query_grid_data(
    variable: str = Query(...),
    region: str = Query(...),
    date: str = Query(...),
    analysis: Optional[str] = Query(None),
    forecast: Optional[int] = Query(None),
    level: Optional[int] = Query(None),
    limit: int = Query(100000, ge=1, le=500000),
    grid_repo: GridDataRepository = Depends(get_grid_repo),
):
    """Consulta dados de grade persistidos no SQLite (persistência dupla).

    Complementa os CSVs: permite consultar os pontos da matriz sem depender
    de arquivos no disco.
    """
    rows = grid_repo.query(
        variable=variable,
        region=region.upper(),
        date_str=date,
        analysis=analysis or "",
        forecast=forecast,
        level=level,
        limit=limit,
    )
    return {"rows": rows, "count": len(rows)}


__all__ = ["router"]
