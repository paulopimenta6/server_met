"""Rotas da camada de análise de dados.

Respostas são persistidas em `analysis_results` (SQLite) e re-servidas
como `cached` quando o mesmo cálculo já foi realizado.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server_MET.api.dependencies import (
    build_region,
    get_analysis_repo,
    get_charts,
    get_profiles,
    get_region_summary,
    get_settings,
    get_statistics,
    get_timeseries,
)
from server_MET.core.config import Settings
from server_MET.core.models import (
    AnalysisRequest,
    ChartRequest,
    ProfileRequest,
)
from server_MET.persistence.repositories import AnalysisRepository

router = APIRouter(tags=["analysis"])


@router.post("/analysis/summary")
async def analysis_summary(
    request: AnalysisRequest,
    statistics=Depends(get_statistics),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    region = build_region(request)
    date_str = request.date or statistics.processor.get_date_str()
    ana = request.analysis or statistics.processor.get_current_analysis_hour()

    cached = analysis_repo.latest(
        "summary", request.variable.value, request.level, region.name, date_str, ana
    )
    if cached:
        return cached

    results = statistics.summarize(
        request.variable.value, region, request.level, date_str, ana
    )
    if not results:
        raise HTTPException(status_code=404, detail="Sem dados GRIB disponíveis para a análise")

    payload = {
        "variable": request.variable.value,
        "region": region.name,
        "date": date_str,
        "analysis": ana,
        "results": results,
    }
    analysis_repo.save(
        "summary", payload, request.variable.value, request.level, region.name, date_str, ana
    )
    return payload


@router.post("/analysis/profile")
async def analysis_profile(
    request: ProfileRequest,
    profiles=Depends(get_profiles),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    region = build_region(request)
    date_str = request.date or profiles.processor.get_date_str()
    ana = request.analysis or profiles.processor.get_current_analysis_hour()

    cached = analysis_repo.latest(
        "profile", request.variable.value, None, region.name, date_str, ana
    )
    if cached:
        return cached

    result = profiles.profile(request.variable.value, region, date_str, ana)
    if not result.get("profile"):
        raise HTTPException(status_code=404, detail="Sem dados GRIB disponíveis para o perfil")

    analysis_repo.save(
        "profile", result, request.variable.value, None, region.name, date_str, ana
    )
    return result


@router.post("/analysis/timeseries")
async def analysis_timeseries(
    request: AnalysisRequest,
    series=Depends(get_timeseries),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    region = build_region(request)
    date_str = request.date or series.processor.get_date_str()
    ana = request.analysis or series.processor.get_current_analysis_hour()

    cached = analysis_repo.latest(
        "timeseries", request.variable.value, request.level, region.name, date_str, ana
    )
    if cached:
        return cached

    result = series.timeseries(request.variable.value, region, request.level, date_str, ana)
    if not result.get("series"):
        raise HTTPException(status_code=404, detail="Sem dados GRIB disponíveis para a série")

    analysis_repo.save(
        "timeseries", result, request.variable.value, request.level, region.name, date_str, ana
    )
    return result


@router.post("/analysis/charts")
async def analysis_charts(
    request: ChartRequest,
    settings: Settings = Depends(get_settings),
    charts=Depends(get_charts),
):
    region = build_region(request)
    date_str = request.date or charts.processor.get_date_str()
    ana = request.analysis or charts.processor.get_current_analysis_hour()
    output_dir = str(settings.dir_tmp / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generated = []
    for kind in ("profile", "timeseries", "histogram"):
        filepath = charts.chart(
            kind=kind,
            region=region,
            variable=request.variable.value,
            level=request.level,
            date_str=date_str,
            analysis=ana,
            output_dir=output_dir,
            title=request.title,
            dpi=request.dpi,
        )
        if filepath:
            generated.append(filepath)

    if not generated:
        raise HTTPException(status_code=500, detail="Falha na geração de gráficos")
    return {"charts": generated, "count": len(generated)}


@router.get("/analysis/regions/{region}")
async def analysis_region(
    region: str,
    summary=Depends(get_region_summary),
):
    return summary.summary(region)


__all__ = ["router"]
