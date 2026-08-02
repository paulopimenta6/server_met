"""Constantes globais do sistema meteorológico.

Fonte única para chaves de variáveis, níveis de pressão, horas de análise,
horas de previsão, resoluções e URLs de dados.
"""
from __future__ import annotations

#: Mapeamento de chave interna -> (nome GRIB, tipo de nível).
#: As chaves `wind`/`winds` são calculadas a partir de u/v e não constam aqui.
VAR_MAP: dict[str, tuple[str, str]] = {
    "ps": ("Surface pressure", "surface"),
    "prnm": ("Pressure reduced to MSL", "meanSea"),
    "temp": ("Temperature", "isobaricInhPa"),
    "temps": ("Temperature", "surface"),
    "nuvem": ("Total Cloud Cover", "isobaricInhPa"),
    "chuvaNaoConvec": ("Total Precipitation", "surface"),
    "chuvaConvec": ("Convective precipitation (water)", "surface"),
    "umidadeRel": ("Relative humidity", "isobaricInhPa"),
    "u": ("U component of wind", "isobaricInhPa"),
    "v": ("V component of wind", "isobaricInhPa"),
    "uSupe": ("U component of wind", "heightAboveGround"),
    "vSupe": ("V component of wind", "heightAboveGround"),
}

#: Chaves calculadas (não são variáveis GRIB diretas).
COMPUTED_VARIABLES: tuple[str, ...] = ("wind", "winds")

#: Níveis de pressão padrão (hPa) para snap de níveis solicitados.
PRESSURE_LEVELS: list[int] = [
    150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750,
    800, 850, 900, 925, 950, 975, 1000,
]

#: Horas de análise do ciclo GFS.
ANALYSIS_HOURS: list[str] = ["00", "06", "12", "18"]

#: Horas de previsão baixadas por padrão.
FORECAST_HOURS: list[str] = ["00", "06", "12", "18"]

#: Resoluções suportadas (0.25°, 0.50°, 1.00°).
RESOLUTIONS: list[str] = ["0p25", "0p50", "1p00"]

#: Níveis próximos à superfície usados para vento de superfície.
NEAR_SURFACE_LEVELS: list[int] = [20, 30, 40, 50, 80]

#: URL base do NOMADS (NOAA).
GFS_BASE_URL: str = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs."

#: URL da API JSON de METAR (aviationweather.gov).
NOAA_METAR_URL: str = "https://aviationweather.gov/api/data/metar?ids={}&format=json&hours=2"

#: Unidades exibidas por chave de variável.
UNITS_MAP: dict[str, str] = {
    "temp": "°C",
    "temps": "°C",
    "ps": "hPa",
    "prnm": "hPa",
    "nuvem": "%",
    "umidadeRel": "%",
    "chuvaNaoConvec": "mm",
    "chuvaConvec": "mm",
    "u": "m/s",
    "v": "m/s",
    "wind": "m/s",
    "winds": "m/s",
}

#: Nome amigável em português por chave de variável (títulos e legendas).
VAR_LABELS_PT: dict[str, str] = {
    "ps": "Pressão na superfície",
    "prnm": "Pressão ao nível do mar",
    "temp": "Temperatura",
    "temps": "Temperatura na superfície",
    "nuvem": "Nebulosidade",
    "chuvaNaoConvec": "Chuva acumulada",
    "chuvaConvec": "Chuva convectiva",
    "umidadeRel": "Umidade relativa",
    "u": "Vento componente U",
    "v": "Vento componente V",
    "uSupe": "Vento componente U (superfície)",
    "vSupe": "Vento componente V (superfície)",
    "wind": "Vento",
    "winds": "Vento na superfície",
}


def var_label(var_name: str) -> str:
    """Rótulo amigável da variável; fallback para a própria chave."""
    return VAR_LABELS_PT.get(var_name, var_name)


__all__ = [
    "VAR_MAP",
    "COMPUTED_VARIABLES",
    "PRESSURE_LEVELS",
    "ANALYSIS_HOURS",
    "FORECAST_HOURS",
    "RESOLUTIONS",
    "NEAR_SURFACE_LEVELS",
    "GFS_BASE_URL",
    "NOAA_METAR_URL",
    "UNITS_MAP",
    "VAR_LABELS_PT",
    "var_label",
]
