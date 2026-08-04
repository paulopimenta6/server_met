#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline principal de processamento - Server MET v2.0
Orquestra: Download → Processamento → Persistência
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import sys

from core.config import (
    GRIB_DIR, ANALYSIS_HOURS, FORECAST_HOURS, RESOLUTIONS,
    REGIOES, NIVEIS_ISOBARICOS, NIVEIS_ALTURA
)
from core.downloader import GribDownloader, download_gribs_main
from core.grib_reader import AutoGribReader
from core.processor import DataProcessor, find_best_level
from core.persistence import persistence
from core.variables import get_all_variable_codes, get_meteorological_variables, get_pollution_variables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class METPipeline:
    def __init__(self):
        self.reader = AutoGribReader(GRIB_DIR)
        self.processor = DataProcessor(self.reader)
    
    async def run_download(self, date_str: str = None) -> List[Path]:
        if date_str is None:
            date_str = datetime.utcnow().strftime("%Y%m%d")
        
        logger.info(f"Starting download for {date_str}")
        async with GribDownloader() as downloader:
            downloaded = await downloader.download_all_for_date(date_str)
        logger.info(f"Download complete: {len(downloaded)} files")
        return downloaded
    
    def get_latest_files(self, date_str: str = None) -> List[Path]:
        if date_str is None:
            date_dirs = sorted([d for d in GRIB_DIR.iterdir() if d.is_dir()], reverse=True)
            if not date_dirs:
                return []
            date_str = date_dirs[0].name
        
        return self.reader.get_latest_analysis_files()
    
    def process_file(
        self,
        file_path: Path,
        region_code: str,
        variables: List[str] = None,
        levels: List[int] = None
    ) -> List[Dict]:
        if variables is None:
            variables = list(get_meteorological_variables().keys()) + ["o3"]
        
        region = REGIOES.get(region_code.upper())
        if not region:
            logger.error(f"Unknown region: {region_code}")
            return []
        
        bounds = (region["lon_min"], region["lon_max"], region["lat_min"], region["lat_max"])
        results = []
        
        for var_code in variables:
            var_levels = levels or get_variable_info(var_code).get("level_values", [])
            
            for level in var_levels:
                best_level = find_best_level(var_levels, level)
                try:
                    extracted = self.processor.extract_variable(
                        str(file_path), var_code, best_level, bounds
                    )
                    
                    if extracted:
                        matrix, lats, lons = self.processor.data_to_matrix(
                            extracted["data"], extracted["lats"], extracted["lons"]
                        )
                        stats = self.processor.compute_statistics(extracted["data"])
                        
                        grib_id = persistence.save_grib_metadata(
                            file_path=str(file_path),
                            analysis_time=file_path.parent.name,
                            forecast_hour=int(file_path.stem.split("f")[-1]),
                            data_date=file_path.parent.parent.name,
                            resolution="0p25" if "0p25" in str(file_path) else "1p00"
                        )
                        
                        persist_id = persistence.save_processed_data(
                            grib_metadata_id=grib_id,
                            variable_code=var_code,
                            level_type=extracted["level_type"],
                            level_value=best_level,
                            region_code=region_code.upper(),
                            min_value=stats["min"],
                            max_value=stats["max"],
                            mean_value=stats["mean"],
                            data_matrix=matrix,
                            lats=lats,
                            lons=lons
                        )
                        
                        results.append({
                            "persist_id": persist_id,
                            "variable": var_code,
                            "level": best_level,
                            "region": region_code,
                            "stats": stats
                        })
                        logger.info(f"Processed: {var_code} level={best_level} region={region_code} stats={stats}")
                
                except Exception as e:
                    logger.error(f"Error processing {var_code} level={level}: {e}")
        
        return results
    
    def run_full_pipeline(
        self,
        date_str: str = None,
        regions: List[str] = None,
        variables: List[str] = None
    ) -> Dict:
        if date_str is None:
            date_str = datetime.utcnow().strftime("%Y%m%d")
        
        if regions is None:
            regions = list(REGIOES.keys())
        
        logger.info(f"Starting full pipeline for {date_str}")
        
        files = self.get_latest_files(date_str)
        if not files:
            logger.warning(f"No GRIB files found for {date_str}, attempting download...")
            asyncio.run(self.run_download(date_str))
            files = self.get_latest_files(date_str)
        
        if not files:
            logger.error("No GRIB files available after download attempt")
            return {"status": "error", "message": "No GRIB files"}
        
        all_results = []
        for file_path in files:
            for region in regions:
                results = self.process_file(file_path, region, variables)
                all_results.extend(results)
        
        logger.info(f"Pipeline complete. Processed {len(all_results)} variable/level/region combinations")
        return {"status": "success", "processed": len(all_results), "results": all_results}

def get_variable_info(var_code):
    from core.variables import get_variable_info
    return get_variable_info(var_code)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Server MET Pipeline")
    parser.add_argument("--date", help="Date in YYYYMMDD format")
    parser.add_argument("--regions", nargs="+", help="Region codes")
    parser.add_argument("--variables", nargs="+", help="Variable codes")
    parser.add_argument("--download-only", action="store_true", help="Only download GRIBs")
    parser.add_argument("--process-only", action="store_true", help="Only process existing GRIBs")
    args = parser.parse_args()
    
    pipeline = METPipeline()
    
    if args.download_only:
        await pipeline.run_download(args.date)
    elif args.process_only:
        pipeline.run_full_pipeline(args.date, args.regions, args.variables)
    else:
        await pipeline.run_download(args.date)
        pipeline.run_full_pipeline(args.date, args.regions, args.variables)

if __name__ == "__main__":
    asyncio.run(main())