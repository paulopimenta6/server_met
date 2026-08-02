"""Rotas de saúde e informações básicas do servidor."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

import server_MET
from server_MET.api.dependencies import get_settings
from server_MET.core.config import Settings
from server_MET.core.models import HealthResponse

router = APIRouter(tags=["health"])

START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    grib_files = list(settings.dir_gribs.rglob("*.f0*"))
    return HealthResponse(
        status="ok",
        version=server_MET.__version__,
        grib_files_available=len(grib_files) > 0,
        uptime=time.time() - START_TIME,
    )


__all__ = ["router"]
