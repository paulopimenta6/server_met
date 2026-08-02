"""Rotas de geração de mapas meteorológicos e animações GIF."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server_MET.api.dependencies import (
    build_region,
    get_animation_generator,
    get_map_generator,
    get_settings,
)
from server_MET.core.config import Settings
from server_MET.core.models import MapRequest

router = APIRouter(tags=["maps"])


@router.post("/maps/generate")
async def generate_map(
    request: MapRequest,
    settings: Settings = Depends(get_settings),
    map_generator=Depends(get_map_generator),
):
    region = build_region(request)
    date_str = request.date or map_generator.processor.get_date_str()
    ana = request.analysis or map_generator.processor.get_current_analysis_hour()
    output_dir = str(settings.dir_tmp / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    fhs = [request.forecast] if request.forecast else None
    files = map_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        forecast_hours=fhs,
        output_dir=output_dir,
        dpi=request.dpi,
        title=request.title,
    )
    if not files:
        raise HTTPException(status_code=500, detail="Falha na geração de mapas")
    return {"maps": files, "count": len(files)}


@router.post("/maps/animate")
async def animate_map(
    request: MapRequest,
    settings: Settings = Depends(get_settings),
    animation_generator=Depends(get_animation_generator),
    duration_ms: Optional[int] = Query(700, ge=100, le=5000, description="Duração de cada quadro (ms)"),
    forecast_hours: Optional[str] = Query(None, description="Horas de previsão separadas por vírgula (ex.: 00,06,12,18)"),
):
    region = build_region(request)
    date_str = request.date or animation_generator.maps.processor.get_date_str()
    ana = request.analysis or animation_generator.maps.processor.get_current_analysis_hour()
    output_dir = str(settings.dir_tmp / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    fhs = None
    if forecast_hours:
        fhs = [h.strip() for h in forecast_hours.split(",") if h.strip()]

    gif_path = animation_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        forecast_hours=fhs,
        output_dir=output_dir,
        duration_ms=duration_ms,
    )
    if not gif_path:
        raise HTTPException(status_code=500, detail="Falha na geração da animação")
    return {"gif": gif_path, "animated": True}


__all__ = ["router"]
