"""Modelos Pydantic v2 e enums usados pela API REST."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MetVariable(str, Enum):
    ps = "ps"
    prnm = "prnm"
    temp = "temp"
    temps = "temps"
    nuvem = "nuvem"
    chuvaNaoConvec = "chuvaNaoConvec"
    chuvaConvec = "chuvaConvec"
    umidadeRel = "umidadeRel"
    u = "u"
    v = "v"
    uSupe = "uSupe"
    vSupe = "vSupe"
    wind = "wind"
    winds = "winds"


class RegionName(str, Enum):
    SP = "SP"
    RJ = "RJ"
    AM = "AM"
    DF = "DF"
    PR = "PR"
    RS = "RS"
    MG = "MG"
    PA = "PA"
    PE = "PE"
    CE = "CE"
    SA = "SA"


class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    png = "png"


class RegionSelection(BaseModel):
    """Formas de seleção de região: nome, bbox ou centro."""

    region: Optional[RegionName] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None


class GribRequest(RegionSelection):
    variable: MetVariable
    level: Optional[int] = Field(default=500, description="Nível de pressão em hPa")
    date: Optional[str] = Field(default=None, description="Data no formato YYYYMMDD")
    analysis: Optional[str] = Field(default=None, description="Hora de análise: 00, 06, 12, 18")
    forecast: Optional[str] = Field(default=None, description="Hora de previsão: 00, 06, 12, 18")
    output_format: OutputFormat = OutputFormat.csv


class MapRequest(GribRequest):
    title: Optional[str] = None
    dpi: int = Field(default=150, ge=72, le=600)


class WindRequest(RegionSelection):
    level: int = Field(default=500, description="Nível de pressão em hPa")
    date: Optional[str] = None
    analysis: Optional[str] = None
    forecast: Optional[str] = None
    output_format: OutputFormat = OutputFormat.csv


class MetarRequest(BaseModel):
    icao_code: str = Field(default="SBGR", description="Código ICAO do aeródromo")
    region: Optional[RegionName] = None


class AnalysisRequest(GribRequest):
    pass


class ProfileRequest(RegionSelection):
    variable: MetVariable
    date: Optional[str] = None
    analysis: Optional[str] = None


class ChartRequest(AnalysisRequest):
    title: Optional[str] = None
    dpi: int = Field(default=150, ge=72, le=600)


class DownloadRequest(BaseModel):
    date_str: Optional[str] = None
    analysis_hour: Optional[str] = None
    resolutions: Optional[list[str]] = None
    forecast_hours: Optional[list[str]] = None
    force: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str
    grib_files_available: bool
    uptime: float


class TaskStatusResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None


class DbStatusResponse(BaseModel):
    db_path: str
    tables: dict[str, int]


__all__ = [
    "MetVariable",
    "RegionName",
    "OutputFormat",
    "RegionSelection",
    "GribRequest",
    "MapRequest",
    "WindRequest",
    "MetarRequest",
    "AnalysisRequest",
    "ProfileRequest",
    "ChartRequest",
    "DownloadRequest",
    "HealthResponse",
    "TaskStatusResponse",
    "DbStatusResponse",
]
