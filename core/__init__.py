#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core package for Server MET v2.0
"""
from core.config import *
from core.variables import *
from core.persistence import persistence, PersistenceManager
from core.regions import RegioesPredefinidas, PontoRegiao, get_regioes_instance

__all__ = [
    "BASE_DIR", "DATA_DIR", "GRIB_DIR", "SQLITE_DIR", "CSV_DIR", "MAPS_DIR",
    "NOAA_BASE_URL", "ANALYSIS_HOURS", "FORECAST_HOURS", "RESOLUTIONS",
    "REGIOES", "NIVEIS_ISOBARICOS", "NIVEIS_SUPERFICIE", "NIVEIS_ALTURA",
    "SQLITE_DB_PATH", "CSV_EXPORT_DIR",
    "DOWNLOAD_TIMEOUT", "DOWNLOAD_MAX_RETRIES", "DOWNLOAD_RETRY_BACKOFF",
    "LOG_LEVEL", "API_HOST", "API_PORT", "API_WORKERS",
    "SCHEDULER_TIMEZONE", "PIPELINE_SCHEDULE_HOURS",
    "VARIABLES_MET", "VARIABLE_CATEGORIES",
    "get_variable_info", "get_variables_by_category", "get_all_variable_codes",
    "get_pollution_variables", "get_meteorological_variables",
    "get_level_values", "get_level_type", "convert_value",
    "persistence", "PersistenceManager",
    "RegioesPredefinidas", "PontoRegiao", "get_regioes_instance",
]