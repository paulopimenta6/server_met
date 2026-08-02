"""Rotas de METAR: consulta por região/ICAO, histórico e estações."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from server_MET.acquisition.metar_client import AERODROMOS
from server_MET.api.dependencies import get_metar_client, get_metar_repo
from server_MET.core.models import MetarRequest
from server_MET.persistence.repositories import MetarRepository

router = APIRouter(tags=["metar"])


@router.post("/metar/fetch")
async def fetch_metar(
    request: MetarRequest,
    metar_client=Depends(get_metar_client),
):
    if request.region:
        region_name = request.region.value
        result = metar_client.get_metar_for_region(region_name)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"METAR indisponível para {region_name}"
            )
        return result
    if request.icao_code:
        data = metar_client.get_metar(request.icao_code.upper())
        if data is None:
            raise HTTPException(
                status_code=404, detail=f"METAR indisponível para {request.icao_code}"
            )
        return data
    raise HTTPException(status_code=400, detail="Informe 'region' ou 'icao_code'")


@router.get("/metar/all")
async def get_all_metars(metar_client=Depends(get_metar_client)):
    results = metar_client.get_all_metars()
    return {"metars": results, "count": len(results)}


@router.get("/metar/stations")
async def list_metar_stations():
    return {"stations": AERODROMOS}


@router.get("/metar/history")
async def metar_history(
    icao: Optional[str] = None,
    limit: int = 100,
    metar_repo: MetarRepository = Depends(get_metar_repo),
):
    rows = metar_repo.list(icao=icao, limit=limit)
    for r in rows:
        r.pop("id", None)
    return {"observations": rows, "count": len(rows)}


__all__ = ["router"]
