"""Constantes globais do sistema meteorológico.

Fonte única para chaves de variáveis, níveis de pressão, horas de análise,
horas de previsão, resoluções e URLs de dados.
"""
from __future__ import annotations

#: Mapeamento de chave interna -> (nome GRIB, tipo de nível).
#: As chaves `wind`/`winds` são calculadas a partir de u/v e não constam aqui.
#: Para variáveis com nível fixo (superfície, 2 m, 10 m, 100 m, 80 m...),
#: o nível é definido em `VAR_FIXED_LEVEL`.
VAR_MAP: dict[str, tuple[str, str]] = {
    "ps": ("Surface pressure", "surface"),
    "prnm": ("Pressure reduced to MSL", "meanSea"),
    "temp": ("Temperature", "isobaricInhPa"),
    "temps": ("Temperature", "surface"),
    "temps2m": ("2 metre temperature", "heightAboveGround"),
    "dewpoint2m": ("2 metre dewpoint temperature", "heightAboveGround"),
    "rh2m": ("2 metre relative humidity", "heightAboveGround"),
    "aparente": ("Apparent temperature", "heightAboveGround"),
    "nuvem": ("Total Cloud Cover", "atmosphere"),
    "nuvemTot": ("Total Cloud Cover", "atmosphere"),
    "gh": ("Geopotential height", "isobaricInhPa"),
    "omega": ("Vertical velocity (pressure)", "isobaricInhPa"),
    "vortabs": ("Absolute vorticity", "isobaricInhPa"),
    "chuvaNaoConvec": ("Total Precipitation", "surface"),
    "chuvaConvec": ("Convective precipitation (water)", "surface"),
    "precipitacao": ("Precipitation rate", "surface"),
    "umidadeRel": ("Relative humidity", "isobaricInhPa"),
    "u": ("U component of wind", "isobaricInhPa"),
    "v": ("V component of wind", "isobaricInhPa"),
    "uSupe": ("10 metre U wind component", "heightAboveGround"),
    "vSupe": ("10 metre V wind component", "heightAboveGround"),
    "vento10u": ("10 metre U wind component", "heightAboveGround"),
    "vento10v": ("10 metre V wind component", "heightAboveGround"),
    "vento100u": ("100 metre U wind component", "heightAboveGround"),
    "vento100v": ("100 metre V wind component", "heightAboveGround"),
    "rajada": ("Wind speed (gust)", "surface"),
    # --- instabilidade e severidade ---
    "cape": ("Convective available potential energy", "surface"),
    "cin": ("Convective inhibition", "surface"),
    "indiceLift": ("Best (4-layer) lifted index", "surface"),
    "helicidade": ("Storm relative helicity", "heightAboveGroundLayer"),
    "indiceHaines": ("Haines Index", "surface"),
    # --- poluição e qualidade do ar ---
    "ozonio": ("Ozone mixing ratio", "isobaricInhPa"),
    "ozonioTot": ("Total ozone", "atmosphereSingleLayer"),
    "aguaPrecipitavel": ("Precipitable water", "atmosphereSingleLayer"),
    "visibilidade": ("Visibility", "surface"),
    "ventilacao": ("Ventilation Rate", "planetaryBoundaryLayer"),
    # --- neve e outras superfícies ---
    "neve": ("Snow depth", "surface"),
}

#: Nível fixo (hPa ou metros) para variáveis que possuem nível próprio,
#: independente do nível solicitado pelo usuário (ex.: 2 m, 10 m, 100 m).
VAR_FIXED_LEVEL: dict[str, int] = {
    "temps2m": 2,
    "dewpoint2m": 2,
    "rh2m": 2,
    "aparente": 2,
    "uSupe": 10,
    "vSupe": 10,
    "vento10u": 10,
    "vento10v": 10,
    "vento100u": 100,
    "vento100v": 100,
    "helicidade": 3000,
}

#: Chaves calculadas (não são variáveis GRIB diretas).
COMPUTED_VARIABLES: tuple[str, ...] = ("wind", "winds")

#: Níveis de pressão padrão (hPa) para snap de níveis solicitados.
#: Corresponde ao conjunto completo de níveis isobáricos do GFS 0.25°.
PRESSURE_LEVELS: list[int] = [
    1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 40, 50, 70, 100, 150, 200, 250,
    300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900,
    925, 950, 975, 1000,
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
    "temps2m": "°C",
    "dewpoint2m": "°C",
    "rh2m": "%",
    "aparente": "°C",
    "ps": "hPa",
    "prnm": "hPa",
    "nuvem": "%",
    "nuvemTot": "%",
    "gh": "m",
    "omega": "Pa/s",
    "vortabs": "s⁻¹",
    "umidadeRel": "%",
    "chuvaNaoConvec": "mm",
    "chuvaConvec": "mm",
    "precipitacao": "mm/h",
    "u": "m/s",
    "v": "m/s",
    "uSupe": "m/s",
    "vSupe": "m/s",
    "vento10u": "m/s",
    "vento10v": "m/s",
    "vento100u": "m/s",
    "vento100v": "m/s",
    "rajada": "m/s",
    "wind": "m/s",
    "winds": "m/s",
    "cape": "J/kg",
    "cin": "J/kg",
    "indiceLift": "K",
    "helicidade": "m²/s²",
    "indiceHaines": "",
    "ozonio": "ppb",
    "ozonioTot": "DU",
    "aguaPrecipitavel": "mm",
    "visibilidade": "km",
    "ventilacao": "m²/s",
    "neve": "cm",
}

#: Nome amigável em português por chave de variável (títulos e legendas).
VAR_LABELS_PT: dict[str, str] = {
    "ps": "Pressão na superfície",
    "prnm": "Pressão ao nível do mar",
    "temp": "Temperatura",
    "temps": "Temperatura na superfície",
    "temps2m": "Temperatura a 2 m",
    "dewpoint2m": "Ponto de orvalho a 2 m",
    "rh2m": "Umidade relativa a 2 m",
    "aparente": "Temperatura aparente",
    "nuvem": "Nebulosidade",
    "nuvemTot": "Nebulosidade total",
    "gh": "Altura geopotencial",
    "omega": "Velocidade vertical (omega)",
    "vortabs": "Vorticidade absoluta",
    "chuvaNaoConvec": "Chuva acumulada",
    "chuvaConvec": "Chuva convectiva",
    "precipitacao": "Taxa de precipitação",
    "umidadeRel": "Umidade relativa",
    "u": "Vento componente U",
    "v": "Vento componente V",
    "uSupe": "Vento componente U (10 m)",
    "vSupe": "Vento componente V (10 m)",
    "vento10u": "Vento U a 10 m",
    "vento10v": "Vento V a 10 m",
    "vento100u": "Vento U a 100 m",
    "vento100v": "Vento V a 100 m",
    "rajada": "Rajada de vento",
    "wind": "Vento",
    "winds": "Vento na superfície",
    "cape": "CAPE (energia potencial)",
    "cin": "CIN (inibição convectiva)",
    "indiceLift": "Índice de levantamento",
    "helicidade": "Helicidade relativa à tempestade",
    "indiceHaines": "Índice de Haines",
    "ozonio": "Ozônio",
    "ozonioTot": "Ozônio total",
    "aguaPrecipitavel": "Água precipitável",
    "visibilidade": "Visibilidade",
    "ventilacao": "Ventilação",
    "neve": "Profundidade de neve",
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
