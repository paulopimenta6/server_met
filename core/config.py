#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração centralizada do Server MET v2.0
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
GRIB_DIR = DATA_DIR / "grib"
SQLITE_DIR = DATA_DIR / "sqlite"
CSV_DIR = DATA_DIR / "csv"
METAR_DIR = DATA_DIR / "metar"
MAPS_DIR = BASE_DIR / "maps"
FRONTEND_DIR = BASE_DIR / "frontend"

for d in [GRIB_DIR, SQLITE_DIR, CSV_DIR, MAPS_DIR, METAR_DIR]:
    d.mkdir(parents=True, exist_ok=True)

NOAA_BASE_URL = os.getenv("NOAA_BASE_URL", "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.")
NOAA_FILTER_URL = os.getenv("NOAA_FILTER_URL", "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl")
AVIATION_WEATHER_URL = os.getenv("AVIATION_WEATHER_URL", "https://aviationweather.gov/api/data/metar")
NOAA_FTP_URL = os.getenv("NOAA_FTP_URL", "ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.")
ANALYSIS_HOURS = ["00", "06", "12", "18"]
FORECAST_HOURS = ["00", "06", "12", "18"]
RESOLUTIONS = ["0p25", "1p00"]

REGIOES = {
    "SP":  {"lon_min": -56, "lon_max": -42, "lat_min": -28, "lat_max": -18},
    "RJ":  {"lon_min": -46, "lon_max": -36, "lat_min": -27, "lat_max": -17},
    "AM":  {"lon_min": -65, "lon_max": -55, "lat_min": -7,  "lat_max": 7},
    "DF":  {"lon_min": -54, "lon_max": -44, "lat_min": -20, "lat_max": -10},
    "PR":  {"lon_min": -54, "lon_max": -44, "lat_min": -30, "lat_max": -20},
    "RS":  {"lon_min": -56, "lon_max": -46, "lat_min": -34, "lat_max": -24},
    "MG":  {"lon_min": -48, "lon_max": -38, "lat_min": -24, "lat_max": -14},
    "PA":  {"lon_min": -53, "lon_max": -43, "lat_min": -6,  "lat_max": 4},
    "PE":  {"lon_min": -39, "lon_max": -29, "lat_min": -13, "lat_max": -3},
    "CE":  {"lon_min": -43, "lon_max": -33, "lat_min": -8,  "lat_max": 2},
    "SA":  {"lon_min": -100, "lon_max": -20, "lat_min": -60, "lat_max": 25},
    "FOR": {"lon_min": -40, "lon_max": -36, "lat_min": -5,  "lat_max": -2},
    "REC": {"lon_min": -36, "lon_max": -34, "lat_min": -9,  "lat_max": -7},
    "SSA": {"lon_min": -39, "lon_max": -37, "lat_min": -14, "lat_max": -11},
    "BEL": {"lon_min": -49, "lon_max": -47, "lat_min": -2,  "lat_max": 1},
    "BH":  {"lon_min": -45, "lon_max": -42, "lat_min": -21, "lat_max": -18},
    "CWB": {"lon_min": -50, "lon_max": -48, "lat_min": -26, "lat_max": -24},
    "POA": {"lon_min": -52, "lon_max": -50, "lat_min": -31, "lat_max": -29},
}

NIVEIS_ISOBARICOS = [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10]
NIVEIS_SUPERFICIE = ["surface", "meanSea"]
NIVEIS_ALTURA = [10, 20, 30, 40, 50, 80, 100]

SQLITE_DB_PATH = SQLITE_DIR / "met_data.db"
CSV_EXPORT_DIR = CSV_DIR

DOWNLOAD_TIMEOUT = 300
DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_RETRY_BACKOFF = 5

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_WORKERS = int(os.getenv("API_WORKERS", "4"))

SCHEDULER_TIMEZONE = "America/Sao_Paulo"
PIPELINE_SCHEDULE_HOURS = [0, 6, 12, 18]