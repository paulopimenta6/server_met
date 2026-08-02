"""Aplicação FastAPI modular do servidor meteorológico.

Entrypoint: `server_MET.api.app:app` (uvicorn).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import server_MET
from server_MET.api.routers import (
    analysis,
    catalog,
    files,
    gribs,
    health,
    history,
    maps,
    matrices,
    metar,
    scheduler,
)
from server_MET.core.config import Settings
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.database import get_database

logger = get_logger(__name__)

WEB_STATIC = Path(__file__).resolve().parent.parent / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    settings.ensure_dirs()
    db = get_database()
    db.migrate()

    scheduler_runner = None
    if settings.scheduler_enabled:
        from server_MET.acquisition.scheduler import get_scheduler_runner

        scheduler_runner = get_scheduler_runner()
        scheduler_runner.start()
        logger.info("Captação contínua iniciada (GRIB + METAR).")

    logger.info(
        "MET Server %s iniciado (banco: %s)",
        server_MET.__version__,
        db.db_path,
    )
    yield
    if scheduler_runner is not None:
        scheduler_runner.stop()
        logger.info("Captação contínua encerrada.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MET Server — GFS Weather Data Server",
        description=(
            "Captação, tratamento, análise e distribuição de dados meteorológicos "
            "do modelo GFS (NOAA) com persistência SQLite e site interativo."
        ),
        version=server_MET.__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(gribs.router)
    app.include_router(maps.router)
    app.include_router(matrices.router)
    app.include_router(analysis.router)
    app.include_router(metar.router)
    app.include_router(files.router)
    app.include_router(history.router)
    app.include_router(scheduler.router)

    app.mount("/static", StaticFiles(directory=str(WEB_STATIC)), name="static")

    @app.get("/", include_in_schema=False)
    async def site_root():
        """Site interativo (mapas, animações, estatísticas e METAR)."""
        return FileResponse(WEB_STATIC / "index.html")

    @app.get("/info", tags=["info"])
    async def info():
        return {
            "name": "MET Server",
            "version": server_MET.__version__,
            "docs": "/docs",
            "health": "/health",
            "site": "/",
        }

    return app


app = create_app()


__all__ = ["app", "create_app"]
