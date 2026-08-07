#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registry de variáveis meteorológicas e de poluição do Server MET v2.0
Mapeamento: código interno -> nome GRIB + tipo nível + conversão de unidade
"""
from typing import Dict, Any, Callable, Optional

def conv_k_to_c(x): return x - 273.15
def conv_pa_to_hpa(x): return x / 100
def conv_kgkg_to_ppbv(x): return x * 1e9
def conv_kgm2_to_mm(x): return x
def conv_kgm2s_to_mmh(x): return x * 3600  # kg m-2 s-1 (Precipitation rate) -> mm/h
def conv_kgkg_to_gkg(x): return x * 1000   # kg kg-1 (mixing ratios) -> g kg-1
def identity(x): return x

VARIABLES_MET: Dict[str, Dict[str, Any]] = {
    "ps": {
        "grib_name": "Surface pressure",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": conv_pa_to_hpa,
        "unit": "hPa",
        "description": "Pressão na superfície",
        "category": "pressure",
    },
    "prnm": {
        "grib_name": "Pressure reduced to MSL",
        "level_type": "meanSea",
        "level_values": [0],
        "unit_conv": conv_pa_to_hpa,
        "unit": "hPa",
        "description": "Pressão reduzida ao nível do mar",
        "category": "pressure",
    },
    "temp": {
        "grib_name": "Temperature",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": conv_k_to_c,
        "unit": "°C",
        "description": "Temperatura em níveis isobáricos",
        "category": "temperature",
    },
    "temps": {
        "grib_name": "Temperature",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": conv_k_to_c,
        "unit": "°C",
        "description": "Temperatura na superfície",
        "category": "temperature",
    },
    "nuvem": {
        "grib_name": "Total Cloud Cover",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": identity,
        "unit": "%",
        "description": "Nebulosidade total",
        "category": "cloud",
    },
    "chuvaNaoConvec": {
        "grib_name": "Total Precipitation",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": conv_kgm2_to_mm,
        "unit": "mm",
        "description": "Precipitação total (não convectiva)",
        "category": "precipitation",
    },
    "chuvaConvec": {
        "grib_name": "Convective precipitation",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": conv_kgm2_to_mm,
        "unit": "mm",
        "description": "Precipitação convectiva",
        "category": "precipitation",
    },
    "umidadeRel": {
        "grib_name": "Relative humidity",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": identity,
        "unit": "%",
        "description": "Umidade relativa",
        "category": "humidity",
    },
    "u": {
        "grib_name": "U component of wind",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Componente U do vento (isobárico)",
        "category": "wind",
    },
    "v": {
        "grib_name": "V component of wind",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Componente V do vento (isobárico)",
        "category": "wind",
    },
    "uSupe": {
        "grib_name": "U component of wind",
        "level_type": "heightAboveGround",
        "level_values": [10, 20, 30, 40, 50, 80, 100],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Componente U do vento (altura acima do solo)",
        "category": "wind",
    },
    "vSupe": {
        "grib_name": "V component of wind",
        "level_type": "heightAboveGround",
        "level_values": [10, 20, 30, 40, 50, 80, 100],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Componente V do vento (altura acima do solo)",
        "category": "wind",
    },
    "vento": {
        "grib_name": "Wind speed",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Vento resultante (magnitude) em níveis isobáricos, calculado a partir das componentes u e v",
        "category": "wind",
        "derived": ["u", "v"],
    },
    "ventoSup": {
        "grib_name": "Wind speed",
        "level_type": "heightAboveGround",
        "level_values": [10, 20, 30, 40, 50, 80, 100],
        "unit_conv": identity,
        "unit": "m/s",
        "description": "Vento resultante (magnitude) em alturas acima do solo, calculado a partir de uSupe e vSupe",
        "category": "wind",
        "derived": ["uSupe", "vSupe"],
    },
    "precipRate": {
        "grib_name": "Precipitation rate",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": conv_kgm2s_to_mmh,
        "unit": "mm/h",
        "description": "Taxa de precipitação instantânea",
        "category": "precipitation",
    },
    "categChuva": {
        "grib_name": "Categorical rain",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": identity,
        "unit": "0/1",
        "description": "Chuva categórica (0 = sem chuva, 1 = chuva)",
        "category": "precipitation",
    },
    "nuvemMistura": {
        "grib_name": "Cloud mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10],
        "unit_conv": conv_kgkg_to_gkg,
        "unit": "g/kg",
        "description": "Razão de mistura de nuvens (água de nuvem em níveis isobáricos)",
        "category": "cloud",
    },
    "o3": {
        "grib_name": "Ozone mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10, 7, 5, 3, 2, 1],
        "unit_conv": conv_kgkg_to_ppbv,
        "unit": "ppbv",
        "description": "Razão de mistura de ozônio",
        "category": "pollution",
    },
    "total_o3": {
        "grib_name": "Total ozone",
        "level_type": "atmosphereSingleLayer",
        "level_values": [0],
        "unit_conv": identity,
        "unit": "DU",
        "description": "Ozônio total na coluna atmosférica (unidade Dobson)",
        "category": "pollution",
    },
    "no2": {
        "grib_name": "Nitrogen dioxide mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10, 7, 5, 3, 2, 1],
        "unit_conv": conv_kgkg_to_ppbv,
        "unit": "ppbv",
        "description": "Razão de mistura de dióxido de nitrogênio",
        "category": "pollution",
        "experimental": True,
    },
    "so2": {
        "grib_name": "Sulfur dioxide mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10, 7, 5, 3, 2, 1],
        "unit_conv": conv_kgkg_to_ppbv,
        "unit": "ppbv",
        "description": "Razão de mistura de dióxido de enxofre",
        "category": "pollution",
        "experimental": True,
    },
    "co": {
        "grib_name": "Carbon monoxide mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10, 7, 5, 3, 2, 1],
        "unit_conv": conv_kgkg_to_ppbv,
        "unit": "ppbv",
        "description": "Razão de mistura de monóxido de carbono",
        "category": "pollution",
        "experimental": True,
    },
    "pm25": {
        "grib_name": "PM2.5",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": identity,
        "unit": "µg/m³",
        "description": "Material particulado fino (PM2.5)",
        "category": "pollution",
        "experimental": True,
    },
    "pm10": {
        "grib_name": "PM10",
        "level_type": "surface",
        "level_values": [0],
        "unit_conv": identity,
        "unit": "µg/m³",
        "description": "Material particulado inalável (PM10)",
        "category": "pollution",
        "experimental": True,
    },
    "aod": {
        "grib_name": "Aerosol optical depth",
        "level_type": "atmosphere",
        "level_values": [0],
        "unit_conv": identity,
        "unit": "",
        "description": "Profundidade óptica de aerossóis",
        "category": "pollution",
        "experimental": True,
    },
    "dust": {
        "grib_name": "Dust mixing ratio",
        "level_type": "isobaricInhPa",
        "level_values": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10, 7, 5, 3, 2, 1],
        "unit_conv": conv_kgkg_to_ppbv,
        "unit": "ppbv",
        "description": "Razão de mistura de poeira",
        "category": "pollution",
        "experimental": True,
    },
}

VARIABLE_CATEGORIES = {
    "pressure": ["ps", "prnm"],
    "temperature": ["temp", "temps"],
    "cloud": ["nuvem", "nuvemMistura"],
    "precipitation": ["chuvaNaoConvec", "chuvaConvec", "precipRate", "categChuva"],
    "humidity": ["umidadeRel"],
    "wind": ["u", "v", "uSupe", "vSupe", "vento", "ventoSup"],
    "pollution": ["o3", "total_o3", "no2", "so2", "co", "pm25", "pm10", "aod", "dust"],
}

# Variables confirmed present in the GFS pgrb2 0p25 product, cross-checked
# against the file inventory `varMET` at the project root and verified live
# against the NOAA filter endpoint. Pollution available there: Ozone mixing
# ratio (o3) and Total ozone (total_o3) only. Precipitation availability:
# Precipitation rate (precipRate), Total precipitation (chuvaNaoConvec, APCP)
# and Categorical rain (categChuva) are present from f006 onwards; Cloud
# mixing ratio (nuvemMistura) is present on isobaric levels. vento/ventoSup
# are derived from the u/v wind components.
AVAILABLE_IN_GFS = {
    "ps", "prnm", "temp", "temps", "nuvem", "nuvemMistura", "umidadeRel",
    "u", "v", "uSupe", "vSupe", "vento", "ventoSup",
    "precipRate", "chuvaNaoConvec", "categChuva",
    "o3", "total_o3",
}

def is_variable_available(var_code: str) -> bool:
    return var_code in AVAILABLE_IN_GFS

def get_available_variables() -> dict:
    return {k: v for k, v in VARIABLES_MET.items() if is_variable_available(k)}

def get_variable_info(var_code: str) -> Optional[Dict[str, Any]]:
    return VARIABLES_MET.get(var_code)

def get_variables_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    codes = VARIABLE_CATEGORIES.get(category, [])
    return {k: v for k, v in VARIABLES_MET.items() if k in codes}

def get_all_variable_codes() -> list:
    return list(VARIABLES_MET.keys())

def get_pollution_variables() -> Dict[str, Dict[str, Any]]:
    return get_variables_by_category("pollution")

def get_meteorological_variables() -> Dict[str, Dict[str, Any]]:
    result = {}
    for cat in ["pressure", "temperature", "cloud", "precipitation", "humidity", "wind"]:
        result.update(get_variables_by_category(cat))
    return result

def get_level_values(var_code: str) -> list:
    info = get_variable_info(var_code)
    return info.get("level_values", []) if info else []

def get_level_type(var_code: str) -> Optional[str]:
    info = get_variable_info(var_code)
    return info.get("level_type") if info else None

def convert_value(var_code: str, value: float) -> float:
    info = get_variable_info(var_code)
    if info and info["unit_conv"]:
        return info["unit_conv"](value)
    return value