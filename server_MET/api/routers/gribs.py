"""Rotas de GRIB: listagem, informações e download (background com status)."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from server_MET.api.dependencies import (
    get_downloader,
    get_processor,
    get_reader,
    get_settings,
    get_task_repo,
)
from server_MET.core.config import Settings
from server_MET.core.models import DownloadRequest, GribRequest, TaskStatusResponse
from server_MET.persistence.repositories import TaskRepository

router = APIRouter(tags=["gribs"])


@router.get("/gribs/list")
async def list_grib_files(
    date: Optional[str] = None,
    settings: Settings = Depends(get_settings),
):
    base = settings.dir_gribs
    if date:
        base = base / date
    if not base.exists():
        return {"gribs": [], "count": 0}
    files = []
    for f in base.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            files.append(str(f.relative_to(settings.dir_gribs)))
    return {"gribs": files, "count": len(files)}


@router.post("/gribs/download")
async def download_gribs(
    background_tasks: BackgroundTasks,
    task_repo: TaskRepository = Depends(get_task_repo),
    downloader=Depends(get_downloader),
    date_str: Optional[str] = Query(None, description="Data YYYYMMDD"),
    analysis_hour: Optional[str] = Query(None, description="Hora de análise 00/06/12/18"),
    resolutions: Optional[str] = Query(None, description="Resoluções separadas por vírgula: 0p25,0p50,1p00"),
    force: bool = Query(False, description="Força redownload mesmo se o arquivo existir"),
):
    task_id = task_repo.create(
        "download",
        {
            "date_str": date_str,
            "analysis_hour": analysis_hour,
            "resolutions": resolutions,
            "force": force,
        },
    )

    def _run():
        task_repo.update(task_id, status="running")
        try:
            res_list = None
            if resolutions:
                res_list = [r.strip() for r in resolutions.split(",") if r.strip()]
            files = downloader.download_gribs_all_resolutions(
                date_str=date_str,
                analysis_hour=analysis_hour,
                resolutions=res_list,
                force=force,
            )
            task_repo.update(
                task_id,
                status="done",
                result={
                    "files": {
                        res: [str(f) for f in fs]
                        for res, fs in files.items()
                    },
                    "count": sum(len(fs) for fs in files.values()),
                },
            )
        except Exception as e:
            task_repo.update(task_id, status="failed", error=str(e))

    background_tasks.add_task(_run)
    return {"status": "download_started", "task_id": task_id}


@router.get("/gribs/download/{task_id}", response_model=TaskStatusResponse)
async def download_status(
    task_id: str,
    task_repo: TaskRepository = Depends(get_task_repo),
):
    task = task_repo.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    result = None
    if task.get("result_json"):
        result = json.loads(task["result_json"])
    return TaskStatusResponse(
        task_id=task["id"],
        task_type=task["task_type"],
        status=task["status"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        error=task.get("error"),
        result=result,
    )


@router.post("/gribs/info")
async def grib_info(
    request: GribRequest,
    reader=Depends(get_reader),
    processor=Depends(get_processor),
):
    date_str = request.date or processor.get_date_str()
    ana = request.analysis or processor.get_current_analysis_hour()
    prev = request.forecast or "00"
    f = reader.find_grib_file(date_str, ana, prev)
    if f is None and not request.analysis:
        for alt_ana in reader.find_available_analyses(date_str):
            f = reader.find_grib_file(date_str, alt_ana, prev)
            if f is not None:
                ana = alt_ana
                break
    if f is None:
        raise HTTPException(status_code=404, detail="Arquivo GRIB não encontrado")
    vars_list = reader.list_variables(f)
    return {"file": str(f), "variables": vars_list, "count": len(vars_list)}


__all__ = ["router"]
