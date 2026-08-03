"""Catálogo: variáveis, regiões e visão geral de dados disponíveis."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from server_MET.api.dependencies import get_processor, get_reader, get_settings
from server_MET.core.config import Settings
from server_MET.core.constants import (
    COMPUTED_VARIABLES,
    PRESSURE_LEVELS,
    VAR_FIXED_LEVEL,
    VAR_MAP,
    var_label,
)
from server_MET.core.models import MetVariable
from server_MET.processing.processor import LEVELED_VARIABLES
from server_MET.processing.regions import (
    CIDADES_PREDEFINIDAS,
    PAISES_AMERICA_DO_SUL,
    REGIOES_DESCRICOES,
    REGIOES_PREDEFINIDAS,
)

router = APIRouter(tags=["catalog"])


@router.get("/variables")
async def list_variables():
    variables = [
        {
            "key": k,
            "name": v[0],
            "level_type": v[1],
            "label": var_label(k),
            "leveled": k in LEVELED_VARIABLES,
            "fixed_level": VAR_FIXED_LEVEL.get(k),
        }
        for k, v in VAR_MAP.items()
    ]
    variables += [
        {
            "key": key,
            "name": name,
            "level_type": level_type,
            "label": var_label(key),
            "leveled": level_type == "pressure",
            "fixed_level": None,
        }
        for key, name, level_type in [
            ("wind", "Wind speed (computed from u/v)", "pressure"),
            ("winds", "Wind speed surface (computed from uSupe/vSupe)", "surface"),
        ]
    ]
    return {"variables": variables}


@router.get("/levels")
async def list_levels():
    """Níveis de pressão padrão (hPa) suportados pelas variáveis de nível."""
    return {"levels": PRESSURE_LEVELS, "count": len(PRESSURE_LEVELS)}


@router.get("/catalog/cycles")
async def list_cycles(reader=Depends(get_reader)):
    """Ciclos (data/análise) realmente disponíveis nos arquivos GRIB do disco.

    É a fonte de datas, análises e horas de previsão usada pelos seletores do
    site e como padrão da API quando data/análise não são informadas.
    """
    cycles = reader.available_cycles()
    latest = reader.latest_available_cycle()
    return {
        "cycles": cycles,
        "latest": {"date": latest[0], "analysis": latest[1]} if latest else None,
        "count": len(cycles),
    }


@router.get("/regions")
async def list_regions():
    regions = []
    for k, v in REGIOES_PREDEFINIDAS.items():
        regions.append(
            {
                "name": k,
                "kind": "estado" if k != "SA" else "visao_geral",
                "bounds": list(v),
                "description": REGIOES_DESCRICOES.get(k, ""),
            }
        )
    for k, v in PAISES_AMERICA_DO_SUL.items():
        regions.append(
            {
                "name": k,
                "kind": "pais",
                "bounds": list(v),
                "description": REGIOES_DESCRICOES.get(k, ""),
            }
        )
    for k, (city_name, lon, lat) in CIDADES_PREDEFINIDAS.items():
        regions.append(
            {
                "name": k,
                "kind": "cidade",
                "center": {"lon": lon, "lat": lat},
                "description": REGIOES_DESCRICOES.get(k, city_name),
            }
        )
    return {"regions": regions}


@router.get("/catalog")
async def data_catalog(
    settings: Settings = Depends(get_settings),
    reader=Depends(get_reader),
):
    """Catálogo de dados GRIB disponíveis no disco: datas, análises e resoluções."""
    grib_dir = settings.dir_gribs
    entries = []
    for date_dir in sorted(grib_dir.iterdir()) if grib_dir.exists() else []:
        if not date_dir.is_dir() or not date_dir.name.isdigit():
            continue
        for ana in sorted(date_dir.iterdir()):
            if not ana.is_dir():
                continue
            resolutions = sorted(
                {
                    res
                    for f in ana.iterdir()
                    if f.is_file()
                    for res in ("0p25", "0p50", "1p00")
                    if res in f.name
                }
            )
            if resolutions:
                entries.append(
                    {
                        "date": date_dir.name,
                        "analysis": ana.name,
                        "resolutions": resolutions,
                    }
                )
    return {"entries": entries, "count": len(entries)}


__all__ = ["router"]
