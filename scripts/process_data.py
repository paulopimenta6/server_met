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

from core.config import GRIB_DIR, ANALYSIS_HOURS, REGIOES
from core.downloader import fetch_filtered_grib
from core.grib_reader import GribReader
from core.processor import DataProcessor
from core.persistence import persistence
from core.maps import generate_map
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
    "ps":          [0],
}


def find_latest_cycle(date: str = None, analysis: str = None):
    """Return (date_str, analysis) for a GFS cycle that actually exists on NOAA."""
    if date is None:
        date = datetime.utcnow().strftime("%Y%m%d")
    candidates_dates = [date]
    try:
        candidates_dates.append((datetime.strptime(date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d"))
    except Exception:
        pass
    if analysis:
        for d in candidates_dates:
            for a in [analysis]:
                if _cycle_exists(d, a):
                    return d, a
        raise RuntimeError(f"No GFS cycle found for analysis {analysis}")
    for d in candidates_dates:
        for a in ANALYSIS_HOURS:
            if _cycle_exists(d, a):
                return d, a
    raise RuntimeError("No GFS cycle available on NOAA (check date)")


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


def process_grib(date_str: str, analysis: str, regions, variables) -> dict:
    """Download, extract, persist and map GFS data for the requested set."""
    reader = GribReader(GRIB_DIR)
    processor = DataProcessor(reader)
    results = {"files": 0, "records": 0, "maps": 0, "errors": []}

    for var_code, levels in variables.items():
        for level in levels:
            for region_code in regions:
                try:
                    file_path = fetch_filtered_grib(
                        date_str, analysis, 0, var_code, level, region_code,
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
                        forecast_hour=0, data_date=date_str,
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
                                 date_str, analysis, forecast=0)
                    results["maps"] += 1
                    logger.info("OK %s %s %s lvl=%s min=%.2f max=%.2f",
                                var_code, region_code, analysis, level,
                                stats["min"], stats["max"])

                except Exception as e:
                    results["errors"].append(f"{var_code}/{level}/{region_code}: {e}")
                    logger.error("FAIL %s %s lvl=%s: %s", var_code, region_code, level, e)

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
    parser.add_argument("--analysis", choices=["00", "06", "12", "18"], help="GFS cycle")
    parser.add_argument("--regions", nargs="+", default=["SP", "RJ", "PR", "RS", "MG", "AM"],
                        help="Region codes (default: SP RJ PR RS MG AM)")
    parser.add_argument("--skip-metar", action="store_true", help="Do not fetch METAR")
    args = parser.parse_args()

    date_str, analysis = find_latest_cycle(args.date, args.analysis)
    logger.info("Using GFS cycle: %s %sZ", date_str, analysis)

    regions = [r.upper() for r in args.regions if r.upper() in REGIOES]
    logger.info("Regions: %s", regions)

    grib_results = process_grib(date_str, analysis, regions, DEFAULT_VARIABLES)
    logger.info("GRIB results: %s", grib_results)

    if not args.skip_metar:
        metar_results = process_metar(regions)
        logger.info("METAR results: %s", metar_results)

    grib_errors = len(grib_results["errors"])
    if grib_errors:
        logger.warning("%d GRIB errors", grib_errors)
        for err in grib_results["errors"][:5]:
            logger.warning("  %s", err)


if __name__ == "__main__":
    main()