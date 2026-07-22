from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


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


class GribRequest(BaseModel):
    variable: MetVariable
    level: Optional[int] = Field(default=500, description="Pressure level in hPa")
    region: Optional[RegionName] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None
    date: Optional[str] = Field(
        default=None,
        description="Date in format YYYYMMDD or YYYYMMDDHHPP (with analysis and prev)",
    )
    analysis: Optional[str] = Field(
        default=None, description="Analysis hour: 00, 06, 12, 18"
    )
    forecast: Optional[str] = Field(
        default=None, description="Forecast hour: 00, 06, 12, 18"
    )
    output_format: OutputFormat = OutputFormat.csv


class MetarRequest(BaseModel):
    icao_code: str = Field(default="SBGR", description="ICAO airport code")
    region: Optional[RegionName] = None


class MapRequest(GribRequest):
    title: Optional[str] = None
    dpi: int = Field(default=150, ge=72, le=600)


class WindRequest(BaseModel):
    level: int = Field(default=500, description="Pressure level in hPa")
    region: Optional[RegionName] = None
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lon_min: Optional[float] = None
    lon_max: Optional[float] = None
    date: Optional[str] = None
    output_format: OutputFormat = OutputFormat.csv


class HealthResponse(BaseModel):
    status: str
    version: str
    grib_files_available: bool
    uptime: float
