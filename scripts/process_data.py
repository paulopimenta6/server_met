#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process real GFS + METAR data and populate the SQLite database and maps.

Pipeline:
    1. Download filtered GFS GRIB subsets (region x variable x level) from NOAA.
    2. Extract statistics and persist them in SQLite.
    3. Generate PNG maps for every processed variable/region.
    4. Download live METAR reports and persist them in SQLite.

Usage:
    PYTHONPATH=. python scripts/process_data.py [--date YYYYMMDD] [--analysis 00|06|12|18]
                                               [--regions SP RJ] [--light]
"""
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from core.config import GRIB_DIR, ANALYSIS_HOURS, FORECAST_HOURS, REGIOES
from core.downloader import fetch_filtered_grib
from core.grib_reader import GribReader
from core.processor import DataProcessor
from core.persistence import persistence
from core.maps import generate_map
from core.variables import VARIABLES_MET
import core.metar as metar_mod

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default dataset: representative mix of meteorological + pollution variables.
DEFAULT_VARIABLES = {
    "temp":        [1000, 850, 500],
    "umidadeRel":  [850],
    "u":           [850],
    "v":           [850],
    "o3":          [500],
    "total_o3":    [0],
    "ps":          [0],
}


def build_all_variables_map() -> dict:
    """One representative level per variable from core.variables registry."""
    levels = {}
    for var, info in VARIABLES_MET.items():
        ltype = info["level_type"]
        if ltype == "isobaricInhPa":
            levels[var] = [500 if var == "o3" else 850]
        elif ltype == "heightAboveGround":
            levels[var] = [10]
        else:
            levels[var] = [0]
    return levels


def find_latest_date() -> str:
    """Return the most recent date with at least one available GFS cycle."""
    date = datetime.utcnow().strftime("%Y%m%d")
    candidates = [date]
    try:
        candidates.append((datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d"))
    except Exception:
        pass
    for d in candidates:
        for a in ANALYSIS_HOURS:
            if _cycle_exists(d, a):
                return d
    raise RuntimeError("No GFS cycle available on NOAA (check date)")


def resolve_analyses(date_str: str, requested: Optional[List[str]] = None) -> List[str]:
    """Return the requested GFS cycles that actually exist for the date."""
    if not requested:
        requested = list(ANALYSIS_HOURS)
    available = []
    for a in requested:
        if _cycle_exists(date_str, a):
            available.append(a)
        else:
            logger.warning("Ciclo %sZ não disponível para %s; ignorado", a, date_str)
    if not available:
        raise RuntimeError(f"No GFS cycle found for date {date_str}")
    return available


def _cycle_exists(date: str, analysis: str) -> bool:
    import httpx
    from core.config import NOAA_FILTER_URL
    url = (f"{NOAA_FILTER_URL}?file=gfs.t{analysis}z.pgrb2.0p25.f000"
           f"&dir=%2Fgfs.{date}%2F{analysis}%2Fatmos&var_TMP=on&lev_1000_mb=on")
    try:
        r = httpx.head(url, timeout=20, follow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def process_grib(date_str: str, analysis: str, regions, variables,
                 forecasts=None) -> dict:
    """Download, extract, persist and map GFS data for the requested set."""
    if forecasts is None:
        forecasts = FORECAST_HOURS
    reader = GribReader(GRIB_DIR)
    processor = DataProcessor(reader)
    results = {"files": 0, "records": 0, "maps": 0, "errors": []}

    for forecast in forecasts:
        forecast_hour = int(forecast)
        for var_code, levels in variables.items():
            for level in levels:
                for region_code in regions:
                    try:
                        file_path = fetch_filtered_grib(
                            date_str, analysis, forecast_hour, var_code, level, region_code,
                            out_dir=GRIB_DIR / date_str / analysis,
                        )
                        results["files"] += 1
                        bounds = REGIOES[region_code]
                        region_bounds = (bounds["lon_min"], bounds["lon_max"],
                                         bounds["lat_min"], bounds["lat_max"])

                        extracted = processor.extract_variable(
                            str(file_path), var_code, level, region_bounds)
                        if not extracted or extracted["data"].size == 0:
                            continue

                        stats = processor.compute_statistics(extracted["data"])
                        matrix, lats, lons = processor.data_to_matrix(
                            extracted["data"], extracted["lats"], extracted["lons"])
                        if not matrix or not matrix[0]:
                            continue

                        grib_id = persistence.save_grib_metadata(
                            file_path=str(file_path), analysis_time=analysis,
                            forecast_hour=forecast_hour, data_date=date_str,
                            resolution="0p25",
                        )
                        persistence.save_processed_data(
                            grib_metadata_id=grib_id, variable_code=var_code,
                            level_type=extracted["level_type"], level_value=level,
                            region_code=region_code, min_value=stats["min"],
                            max_value=stats["max"], mean_value=stats["mean"],
                            data_matrix=matrix, lats=lats, lons=lons,
                        )
                        results["records"] += 1

                        generate_map(matrix, lats, lons, var_code, level, region_code,
                                     date_str, analysis, forecast=forecast_hour)
                        results["maps"] += 1
                        logger.info("OK %s %s %s f%03d lvl=%s min=%.2f max=%.2f",
                                    var_code, region_code, analysis, forecast_hour,
                                    level, stats["min"], stats["max"])

                    except Exception as e:
                        results["errors"].append(f"{var_code}/{level}/{region_code}/f{forecast_hour}: {e}")
                        logger.error("FAIL %s %s lvl=%s f%03d: %s", var_code,
                                     region_code, level, forecast_hour, e)

    return results


def process_metar(regions) -> dict:
    """Fetch and store live METAR reports for relevant stations."""
    from core.metar import DEFAULT_STATIONS
    stations = list(DEFAULT_STATIONS.keys())
    try:
        return metar_mod.fetch_and_store(stations=stations)
    except Exception as e:
        logger.error("METAR fetch failed: %s", e)
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Process real GFS + METAR data")
    parser.add_argument("--date", help="GFS date YYYYMMDD (default: latest available)")
    parser.add_argument("--analysis", nargs="*", choices=["00", "06", "12", "18"],
                        default=None, help="GFS cycles (default: all 00 06 12 18)")
    parser.add_argument("--forecast", nargs="+", choices=["00", "06", "12", "18"],
                        default=FORECAST_HOURS,
                        help="GFS forecast hours (default: all f000-f018)")
    parser.add_argument("--regions", nargs="+", default=["SP", "RJ", "PR", "RS", "MG", "AM"],
                        help="Region codes (default: SP RJ PR RS MG AM)")
    parser.add_argument("--all-variables", action="store_true",
                        help="Process every variable in core/variables.py (unavailable ones are skipped)")
    parser.add_argument("--skip-metar", action="store_true", help="Do not fetch METAR")
    args = parser.parse_args()

    date_str = args.date if args.date else find_latest_date()
    logger.info("Using GFS date: %s", date_str)

    analyses = resolve_analyses(date_str, args.analysis)
    logger.info("Analyses: %s", analyses)

    regions = [r.upper() for r in args.regions if r.upper() in REGIOES]
    logger.info("Regions: %s", regions)

    variables = build_all_variables_map() if args.all_variables else DEFAULT_VARIABLES
    logger.info("Variables: %s", variables)
    logger.info("Forecasts: %s", args.forecast)

    aggregate = {"files": 0, "records": 0, "maps": 0, "errors": []}
    for analysis in analyses:
        logger.info("Processando ciclo %sZ de %s", analysis, date_str)
        grib_results = process_grib(date_str, analysis, regions, variables, args.forecast)
        for key in aggregate:
            if key == "errors":
                aggregate[key].extend(grib_results[key])
            else:
                aggregate[key] += grib_results[key]
    logger.info("GRIB results: %s", aggregate)

    if not args.skip_metar:
        metar_results = process_metar(regions)
        logger.info("METAR results: %s", metar_results)

    grib_errors = len(aggregate["errors"])
    if grib_errors:
        logger.warning("%d GRIB errors", grib_errors)
        for err in aggregate["errors"][:5]:
            logger.warning("  %s", err)


if __name__ == "__main__":
    main()