"""Aplicação FastAPI modular do servidor meteorológico.

Entrypoint: `server_MET.api.app:app` (uvicorn).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
)
from server_MET.core.config import Settings
from server_MET.core.logging_conf import get_logger
from server_MET.persistence.database import get_database

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    settings.ensure_dirs()
    db = get_database()
    db.migrate()
    logger.info(
        "MET Server %s iniciado (banco: %s)",
        server_MET.__version__,
        db.db_path,
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="MET Server — GFS Weather Data Server",
        description=(
            "Captação, tratamento, análise e distribuição de dados meteorológicos "
            "do modelo GFS (NOAA) com persistência SQLite."
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

    @app.get("/", tags=["info"])
    async def root():
        return {
            "name": "MET Server",
            "version": server_MET.__version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()


__all__ = ["app", "create_app"]
