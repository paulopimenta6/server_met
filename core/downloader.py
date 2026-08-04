#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloader de arquivos GRIB do NOAA GFS - Server MET v2.0
Substitui o script shell goGribV2.sh
"""
import asyncio
import httpx
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
import logging
from core.config import (
    GRIB_DIR, NOAA_BASE_URL, ANALYSIS_HOURS, FORECAST_HOURS, 
    RESOLUTIONS, DOWNLOAD_TIMEOUT, DOWNLOAD_MAX_RETRIES, DOWNLOAD_RETRY_BACKOFF
)

logger = logging.getLogger(__name__)

class GribDownloader:
    def __init__(self, base_dir: Path = GRIB_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.client = httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True, headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def _get_date_dir(self, date_str: str) -> Path:
        date_dir = self.base_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir
    
    def _get_analysis_dir(self, date_dir: Path, analysis: str) -> Path:
        ana_dir = date_dir / analysis
        ana_dir.mkdir(parents=True, exist_ok=True)
        return ana_dir
    
    def _build_url(self, date_str: str, analysis: str, forecast: str, resolution: str) -> str:
        return f"{NOAA_BASE_URL}{date_str}/{analysis}/atmos/gfs.t{analysis}z.pgrb2.{resolution}.f{forecast}"
    
    def _get_local_path(self, date_dir: Path, analysis: str, forecast: str, resolution: str) -> Path:
        ana_dir = self._get_analysis_dir(date_dir, analysis)
        return ana_dir / f"gfs.t{analysis}z.pgrb2.{resolution}.f{forecast}"
    
    async def _check_url_exists(self, url: str) -> bool:
        try:
            response = await self.client.head(url)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"HEAD request failed for {url}: {e}")
            return False
    
    async def _download_file(self, url: str, local_path: Path, retries: int = DOWNLOAD_MAX_RETRIES) -> bool:
        for attempt in range(retries):
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    local_path.write_bytes(response.content)
                    logger.info(f"Downloaded: {local_path} ({len(response.content)} bytes)")
                    return True
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
            except Exception as e:
                logger.warning(f"Download attempt {attempt+1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(DOWNLOAD_RETRY_BACKOFF * (attempt + 1))
        logger.error(f"Failed to download {url} after {retries} attempts")
        return False
    
    async def download_analysis_forecast(
        self, 
        date_str: str, 
        analysis: str, 
        forecast: str,
        resolutions: List[str] = None
    ) -> List[Path]:
        if resolutions is None:
            resolutions = RESOLUTIONS
        
        date_dir = self._get_date_dir(date_str)
        downloaded = []
        
        for resolution in resolutions:
            url = self._build_url(date_str, analysis, forecast, resolution)
            local_path = self._get_local_path(date_dir, analysis, forecast, resolution)
            
            if local_path.exists():
                logger.info(f"File already exists: {local_path}")
                downloaded.append(local_path)
                continue
            
            if await self._check_url_exists(url):
                if await self._download_file(url, local_path):
                    downloaded.append(local_path)
            else:
                logger.debug(f"URL not found: {url}")
        
        return downloaded
    
    async def download_all_for_date(
        self, 
        date_str: str,
        analyses: List[str] = None,
        forecasts: List[str] = None,
        resolutions: List[str] = None
    ) -> List[Path]:
        if analyses is None:
            analyses = ANALYSIS_HOURS
        if forecasts is None:
            forecasts = FORECAST_HOURS
        if resolutions is None:
            resolutions = RESOLUTIONS
        
        all_downloaded = []
        tasks = []
        
        for analysis in analyses:
            for forecast in forecasts:
                tasks.append(self.download_analysis_forecast(date_str, analysis, forecast, resolutions))
        
        results = await asyncio.gather(*tasks)
        for result in results:
            all_downloaded.extend(result)
        
        return all_downloaded
    
    async def download_latest_cycle(self, resolutions: List[str] = None) -> List[Path]:
        now = datetime.utcnow()
        date_str = now.strftime("%Y%m%d")
        
        current_hour = now.hour
        current_analysis = "00"
        for ah in ANALYSIS_HOURS:
            if current_hour >= int(ah):
                current_analysis = ah
        
        logger.info(f"Downloading latest cycle: {date_str} {current_analysis}Z")
        return await self.download_all_for_date(date_str, analyses=[current_analysis], resolutions=resolutions)

async def download_gribs_main(
    date_str: str = None,
    analyses: List[str] = None,
    forecasts: List[str] = None,
    resolutions: List[str] = None
):
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y%m%d")
    
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting GRIB download for {date_str}")
    
    async with GribDownloader() as downloader:
        downloaded = await downloader.download_all_for_date(date_str, analyses, forecasts, resolutions)
        logger.info(f"Download complete. {len(downloaded)} files downloaded.")
        return downloaded

if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(download_gribs_main(date_arg))