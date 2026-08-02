"""Histórico persistido: downloads, saídas, METAR e status do banco."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from server_MET.api.dependencies import (
    get_analysis_repo,
    get_download_repo,
    get_output_repo,
)
from server_MET.core.config import Settings
from server_MET.core.models import DbStatusResponse
from server_MET.persistence.database import get_database
from server_MET.persistence.repositories import (
    AnalysisRepository,
    DownloadRepository,
    OutputRepository,
)

router = APIRouter(tags=["history"])


@router.get("/history/downloads")
async def history_downloads(
    date_str: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
    repo: DownloadRepository = Depends(get_download_repo),
):
    rows = repo.list(date_str=date_str, status=status, limit=limit)
    return {"downloads": rows, "count": len(rows)}


@router.get("/history/outputs")
async def history_outputs(
    kind: Optional[str] = None,
    region: Optional[str] = None,
    date_str: Optional[str] = None,
    limit: int = 200,
    repo: OutputRepository = Depends(get_output_repo),
):
    rows = repo.list(kind=kind, region=region, date_str=date_str, limit=limit)
    return {"outputs": rows, "count": len(rows)}


@router.get("/history/analysis")
async def history_analysis(
    kind: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 100,
    repo: AnalysisRepository = Depends(get_analysis_repo),
):
    rows = repo.list(kind=kind, region=region, limit=limit)
    return {"analysis": rows, "count": len(rows)}


@router.get("/db/status", response_model=DbStatusResponse)
async def db_status():
    db = get_database()
    return DbStatusResponse(db_path=str(db.db_path), tables=db.table_counts())


__all__ = ["router"]
