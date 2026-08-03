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
    default_cycle,
    get_analysis_repo,
    get_charts,
    get_dashboard,
    get_profiles,
    get_region_summary,
    get_settings,
    get_statistics,
    get_stats_repo,
    get_timeseries,
)
from server_MET.core.config import Settings
from server_MET.core.models import (
    AnalysisRequest,
    ChartRequest,
    ProfileRequest,
)
from server_MET.persistence.repositories import AnalysisRepository, StatisticsRepository

router = APIRouter(tags=["analysis"])


@router.post("/analysis/summary")
async def analysis_summary(
    request: AnalysisRequest,
    statistics=Depends(get_statistics),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    region = build_region(request)
    date_str, ana = default_cycle(statistics.processor, request.date, request.analysis)

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
    date_str, ana = default_cycle(profiles.processor, request.date, request.analysis)

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
    date_str, ana = default_cycle(series.processor, request.date, request.analysis)

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
    date_str, ana = default_cycle(charts.processor, request.date, request.analysis)
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


@router.post("/analysis/dashboard")
async def analysis_dashboard(
    request: AnalysisRequest,
    dashboard=Depends(get_dashboard),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    """Dashboard estatístico: resumo por hora + tendência (OLS) + perfil.

    Persiste as métricas na tabela `statistics` e exporta um CSV em
    `data/analise` (servido em `/files/analise/...`). O JSON completo é
    cacheado em `analysis_results` (kind `dashboard`).
    """
    region = build_region(request)
    date_str, ana = default_cycle(dashboard.processor, request.date, request.analysis)

    cached = analysis_repo.latest(
        "dashboard", request.variable.value, request.level, region.name, date_str, ana
    )
    if cached:
        return cached

    result = dashboard.build(
        request.variable.value, region, request.level, date_str, ana
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Sem dados GRIB disponíveis para o dashboard")

    analysis_repo.save(
        "dashboard", result, request.variable.value, request.level,
        region.name, date_str, ana,
    )
    return result


@router.get("/analysis/dashboard")
async def get_dashboard(
    variable: str = Query(...),
    region: str = Query(...),
    level: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    analysis: Optional[str] = Query(None),
    analysis_repo: AnalysisRepository = Depends(get_analysis_repo),
):
    """Recupera um dashboard já calculado (cache persistido)."""
    cached = analysis_repo.latest(
        "dashboard", variable, level, region.upper(), date, analysis
    )
    if not cached:
        raise HTTPException(status_code=404, detail="Dashboard não encontrado (use POST /analysis/dashboard para gerar)")
    return cached


@router.get("/analysis/statistics")
async def get_statistics_rows(
    variable: str = Query(...),
    region: str = Query(...),
    date: Optional[str] = Query(None),
    analysis: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    stats_repo: StatisticsRepository = Depends(get_stats_repo),
):
    """Consulta as estatísticas descritivas persistidas na tabela `statistics`.

    Cada linha corresponde a uma hora de previsão da variável/região.
    """
    rows = stats_repo.query(
        variable=variable,
        region=region.upper(),
        date_str=date,
        analysis=analysis,
        level=level,
        limit=limit,
    )
    return {"rows": rows, "count": len(rows)}


@router.get("/analysis/regions/{region}")
async def analysis_region(
    region: str,
    summary=Depends(get_region_summary),
):
    return summary.summary(region)


__all__ = ["router"]
