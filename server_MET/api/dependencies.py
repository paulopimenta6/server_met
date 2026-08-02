"""Dependências compartilhadas da API (serviços singleton e helpers)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from server_MET.acquisition.grib_downloader import GribDownloader
from server_MET.acquisition.grib_reader import GribReader
from server_MET.acquisition.metar_client import MetarClient
from server_MET.analysis.charts import AnalysisCharts
from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.summary import RegionSummary
from server_MET.analysis.timeseries import TimeSeriesAnalyzer
from server_MET.core.config import Settings
from server_MET.output.maps import MapGenerator
from server_MET.output.matrices import MatrixGenerator
from server_MET.persistence.repositories import (
    AnalysisRepository,
    DownloadRepository,
    MetarRepository,
    OutputRepository,
    TaskRepository,
)
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import Region

_settings = Settings()

_services: dict = {}


def _get(name: str, factory):
    if name not in _services:
        _services[name] = factory()
    return _services[name]


def get_settings() -> Settings:
    return _settings


def get_reader() -> GribReader:
    return _get("reader", GribReader)


def get_processor() -> DataProcessor:
    return _get("processor", DataProcessor)


def get_downloader() -> GribDownloader:
    return _get("downloader", GribDownloader)


def get_map_generator() -> MapGenerator:
    return _get("map_generator", MapGenerator)


def get_matrix_generator() -> MatrixGenerator:
    return _get("matrix_generator", MatrixGenerator)


def get_metar_client() -> MetarClient:
    return _get("metar_client", MetarClient)


def get_statistics() -> StatisticsAnalyzer:
    return _get("statistics", StatisticsAnalyzer)


def get_profiles() -> ProfileAnalyzer:
    return _get("profiles", ProfileAnalyzer)


def get_timeseries() -> TimeSeriesAnalyzer:
    return _get("timeseries", TimeSeriesAnalyzer)


def get_charts() -> AnalysisCharts:
    return _get("charts", AnalysisCharts)


def get_region_summary() -> RegionSummary:
    return _get("region_summary", RegionSummary)


def get_download_repo() -> DownloadRepository:
    return _get("download_repo", DownloadRepository)


def get_output_repo() -> OutputRepository:
    return _get("output_repo", OutputRepository)


def get_metar_repo() -> MetarRepository:
    return _get("metar_repo", MetarRepository)


def get_task_repo() -> TaskRepository:
    return _get("task_repo", TaskRepository)


def get_analysis_repo() -> AnalysisRepository:
    return _get("analysis_repo", AnalysisRepository)


def build_region(req) -> Region:
    """Constrói uma Region a partir de um modelo com campos de seleção."""
    if req.region:
        return Region(name=req.region.value)
    if all(
        getattr(req, attr, None) is not None
        for attr in ["lon_min", "lon_max", "lat_min", "lat_max"]
    ):
        return Region(
            lon_min=req.lon_min,
            lon_max=req.lon_max,
            lat_min=req.lat_min,
            lat_max=req.lat_max,
        )
    if getattr(req, "lon", None) is not None and getattr(req, "lat", None) is not None:
        return Region(center_lon=req.lon, center_lat=req.lat)
    raise HTTPException(
        status_code=400,
        detail="Informe 'region', bounding box (lon_min/lon_max/lat_min/lat_max) ou centro (lon/lat)",
    )


def resolve_path(kind: str) -> Path:
    """Resolve o diretório raiz de um tipo de artefato (com proteção de caminho)."""
    s = Settings()
    kind_map = {
        "mapas": s.dir_mapas,
        "matrizes": s.dir_matrizes,
        "bluesky": s.dir_matrizes_bluesky,
        "analise": s.dir_analise,
        "tmp": s.dir_tmp,
    }
    if kind not in kind_map:
        raise HTTPException(status_code=400, detail=f"Tipo de artefato inválido: {kind}")
    return kind_map[kind]


def safe_join(base: Path, relative: str) -> Path:
    """Junta `base` com `relative` garantindo que o resultado permaneça dentro de `base`."""
    base = base.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Caminho inválido")
    return target


__all__ = [
    "get_settings",
    "get_reader",
    "get_processor",
    "get_downloader",
    "get_map_generator",
    "get_matrix_generator",
    "get_metar_client",
    "get_statistics",
    "get_profiles",
    "get_timeseries",
    "get_charts",
    "get_region_summary",
    "get_download_repo",
    "get_output_repo",
    "get_metar_repo",
    "get_task_repo",
    "get_analysis_repo",
    "build_region",
    "resolve_path",
    "safe_join",
]
