"""Rotas da captação contínua: status do scheduler e disparo manual."""
from __future__ import annotations

from fastapi import APIRouter

from server_MET.acquisition.scheduler import get_scheduler_runner

router = APIRouter(tags=["scheduler"])


@router.get("/scheduler/status")
async def scheduler_status():
    """Estado da captação contínua (GRIB + METAR)."""
    runner = get_scheduler_runner()
    return runner.status()


@router.post("/scheduler/run-now")
async def scheduler_run_now():
    """Dispara uma verificação imediata de novo ciclo GFS."""
    runner = get_scheduler_runner()
    return {"status": runner.run_now()}


__all__ = ["router"]
