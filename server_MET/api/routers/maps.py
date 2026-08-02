"""Rotas de geração de mapas meteorológicos."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from server_MET.api.dependencies import build_region, get_map_generator, get_settings
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

    files = map_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        output_dir=output_dir,
        dpi=request.dpi,
        title=request.title,
    )
    if not files:
        raise HTTPException(status_code=500, detail="Falha na geração de mapas")
    return {"maps": files, "count": len(files)}


__all__ = ["router"]
