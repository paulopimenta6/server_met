#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Main Application - Server MET v2.0
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from api.routes import health, data, maps, metar
from core.config import API_HOST, API_PORT, FRONTEND_DIR

app = FastAPI(
    title="Server MET API",
    description="Meteorological and Pollution Data API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(data.router, prefix="/api/v1")
app.include_router(maps.router, prefix="/api/v1")
app.include_router(metar.router, prefix="/api/v1")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(FRONTEND_DIR / "index.html")
    
    @app.get("/frontend/{path:path}")
    async def serve_frontend_files(path: str):
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/v1/info")
async def api_info():
    return {
        "name": "Server MET API",
        "version": "2.0.0",
        "description": "Meteorological and Pollution Data Server",
        "endpoints": {
            "health": "/health",
            "data": "/api/v1/data",
            "maps": "/api/v1/maps",
            "metar": "/api/v1/metar",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)