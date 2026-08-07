#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG map generation for GRIB-derived data using matplotlib + Basemap.
"""
from pathlib import Path
from typing import List

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

from core.config import MAPS_DIR

# Variables that have isobaric levels
ISOBARIC_VARIABLES = {
    "temp":       {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "RdBu_r", "unit": "°C"},
    "umidadeRel": {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "Blues", "unit": "%"},
    "nuvem":      {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "Greys", "unit": "%"},
    "u":          {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "RdBu", "unit": "m/s"},
    "v":          {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "RdBu", "unit": "m/s"},
    "vento":      {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "viridis", "unit": "m/s"},
    "nuvemMistura": {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "Greys", "unit": "g/kg"},
    "o3":         {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "OrRd", "unit": "ppbv"},
    "no2":        {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "OrRd", "unit": "ppbv"},
    "so2":        {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "OrRd", "unit": "ppbv"},
    "co":         {"levels": [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], "cmap": "OrRd", "unit": "ppbv"},
}

SURFACE_VARIABLES = {
    "ps":            {"cmap": "YlOrRd", "unit": "hPa"},
    "prnm":          {"cmap": "YlOrRd", "unit": "hPa"},
    "temps":         {"cmap": "RdBu_r", "unit": "°C"},
    "chuvaNaoConvec": {"cmap": "Blues", "unit": "mm"},
    "chuvaConvec":   {"cmap": "Blues", "unit": "mm"},
    "precipRate":    {"cmap": "Blues", "unit": "mm/h"},
    "categChuva":    {"cmap": "Blues", "unit": "0/1"},
    "pm25":          {"cmap": "OrRd", "unit": "µg/m³"},
    "pm10":          {"cmap": "OrRd", "unit": "µg/m³"},
    "aod":           {"cmap": "YlOrBr", "unit": ""},
    "uSupe":         {"cmap": "RdBu", "unit": "m/s"},
    "vSupe":         {"cmap": "RdBu", "unit": "m/s"},
    "ventoSup":      {"cmap": "viridis", "unit": "m/s"},
    "total_o3":      {"cmap": "viridis", "unit": "DU"},
}


def _var_config(variable: str) -> dict:
    if variable in ISOBARIC_VARIABLES:
        return ISOBARIC_VARIABLES[variable]
    if variable in SURFACE_VARIABLES:
        return SURFACE_VARIABLES[variable]
    return {"cmap": "viridis", "unit": ""}


def generate_map(data, lats, lons, variable, level, region, date_str,
                 analysis, forecast, out_dir: Path = MAPS_DIR, cmap=None, unit=None) -> Path:
    """Generate and save a PNG map for the given data matrix."""
    conf = _var_config(variable)
    cmap = cmap or conf["cmap"]
    unit = unit if unit is not None else conf["unit"]

    lats = np.asarray(lats, dtype=float)
    lons = np.asarray(lons, dtype=float)
    data = np.asarray(data, dtype=float)

    lon_2d, lat_2d = np.meshgrid(lons, lats)
    lon_min, lon_max = float(lons.min()), float(lons.max())
    lat_min, lat_max = float(lats.min()), float(lats.max())

    plt.figure(figsize=(12, 10))
    m = Basemap(projection="mill",
                llcrnrlat=lat_min, urcrnrlat=lat_max,
                llcrnrlon=lon_min, urcrnrlon=lon_max,
                resolution="i")
    x, y = m(lon_2d, lat_2d)

    vmin, vmax = float(np.nanmin(data)), float(np.nanmax(data))
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        plt.close()
        raise ValueError("Data has no finite values")

    cs = m.contourf(x, y, data, levels=30, cmap=cmap, vmin=vmin, vmax=vmax)
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries(linewidth=0.3)
    m.drawstates(linewidth=0.2)
    m.drawparallels(np.arange(int(np.ceil(lat_min)), int(lat_max) + 1, 4),
                    labels=[1, 0, 0, 0], fontsize=8)
    m.drawmeridians(np.arange(int(np.ceil(lon_min)), int(lon_max) + 1, 4),
                    labels=[0, 0, 0, 1], fontsize=8)

    cbar = plt.colorbar(cs, orientation="horizontal", pad=0.05, shrink=0.8)
    cbar.set_label(unit)

    level_str = f"{variable.upper()} - {level} hPa" if level and level > 0 else f"{variable.upper()} - Superfície"
    plt.title(f"GFS 0.25° - {region} - {level_str}\nData: {date_str} Análise: {analysis}Z Previsão: f{forecast:03d}",
              fontsize=10)

    out_dir.mkdir(parents=True, exist_ok=True)
    level_file = str(level) if level and level > 0 else "SFC"
    filename = f"GFS_0p25_{region.upper()}_N{level_file}_{variable}_{analysis}_{date_str}_{forecast:03d}.png"
    filepath = out_dir / filename
    plt.savefig(filepath, dpi=100, bbox_inches="tight", facecolor="white")
    plt.close()
    return filepath