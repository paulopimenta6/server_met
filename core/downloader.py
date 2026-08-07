#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloader de arquivos GRIB do NOAA GFS - Server MET v2.0
Baseado no script shell goGribV2.sh original
Usa HTTPS (nomads.ncep.noaa.gov) conforme script original
"""
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import List, Optional
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
        # URL base HTTPS do NOAA (conforme goGribV2.sh)
        self.base_url = NOAA_BASE_URL
    
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
    
    def _format_forecast(self, forecast: str) -> str:
        """Formata hora de previsão para padrão f000/f006/f012/f018 (sempre 3 dígitos)."""
        return f"f{int(forecast):03d}"
    
    def _build_url(self, date_str: str, analysis: str, forecast: str, resolution: str) -> str:
        """Constrói URL seguindo padrão exato do goGribV2.sh: gfs.t{analysis}z.pgrb2.{resolution}.f0{forecast}"""
        forecast_fmt = self._format_forecast(forecast)
        return f"{self.base_url}{date_str}/{analysis}/atmos/gfs.t{analysis}z.pgrb2.{resolution}.{forecast_fmt}"
    
    def _get_local_path(self, date_dir: Path, analysis: str, forecast: str, resolution: str) -> Path:
        ana_dir = self._get_analysis_dir(date_dir, analysis)
        forecast_fmt = self._format_forecast(forecast)
        return ana_dir / f"gfs.t{analysis}z.pgrb2.{resolution}.{forecast_fmt}"
    
    async def _check_url_exists(self, url: str) -> bool:
        """Verifica se URL existe (equivalente ao wget --spider)"""
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
        """Baixa arquivos para uma análise e previsão específica (todas as resoluções)"""
        if resolutions is None:
            resolutions = RESOLUTIONS
        
        date_dir = self._get_date_dir(date_str)
        downloaded = []
        
        for resolution in resolutions:
            local_path = self._get_local_path(date_dir, analysis, forecast, resolution)
            
            if local_path.exists():
                logger.info(f"Arquivo já existe: {local_path}")
                downloaded.append(local_path)
                continue
            
            url = self._build_url(date_str, analysis, forecast, resolution)
            logger.info(f"Verificando: {url}")
            
            # Spider check (equivalente ao wget --spider)
            if await self._check_url_exists(url):
                logger.info(f"Site OK! Fazendo download...")
                if await self._download_file(url, local_path):
                    downloaded.append(local_path)
            else:
                logger.warning(f"Arquivo não encontrado: {url}")
        
        return downloaded
    
    async def download_all_for_date(
        self, 
        date_str: str,
        analyses: List[str] = None,
        forecasts: List[str] = None,
        resolutions: List[str] = None
    ) -> List[Path]:
        """Baixa todos os arquivos para uma data (loop aninhado igual ao shell script)"""
        if analyses is None:
            analyses = ANALYSIS_HOURS
        if forecasts is None:
            forecasts = FORECAST_HOURS
        if resolutions is None:
            resolutions = RESOLUTIONS
        
        all_downloaded = []
        
        # Loop igual ao shell script: for tAnalise in 00 06 12 18
        for analysis in analyses:
            # Loop igual ao shell script: for tPrev in 00 06 12 18
            for forecast in forecasts:
                downloaded = await self.download_analysis_forecast(date_str, analysis, forecast, resolutions)
                all_downloaded.extend(downloaded)
        
        return all_downloaded
    
    async def download_latest_cycle(self, resolutions: List[str] = None) -> List[Path]:
        """Baixa apenas o ciclo mais recente baseado na hora atual"""
        now = datetime.utcnow()
        date_str = now.strftime("%Y%m%d")
        
        current_hour = now.hour
        current_analysis = "00"
        for ah in ANALYSIS_HOURS:
            if current_hour >= int(ah):
                current_analysis = ah
        
        logger.info(f"Baixando ciclo mais recente: {date_str} {current_analysis}Z")
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
    logger.info(f"Iniciando download GRIB para {date_str}")
    
    async with GribDownloader() as downloader:
        downloaded = await downloader.download_all_for_date(date_str, analyses, forecasts, resolutions)
        logger.info(f"Download completo. {len(downloaded)} arquivos baixados.")
        return downloaded


# --------------------------------------------------------------------------- #
# Filtered GFS fetch (lightweight - downloads only the required region/variable)
# --------------------------------------------------------------------------- #
from core.config import NOAA_FILTER_URL, REGIOES  # noqa: E402

# registry code -> (NOAA GRIB shortName, typeOfLevel)
NOAA_FILTER_VARS = {
    "temp":          ("TMP",   "isobaricInhPa"),
    "umidadeRel":    ("RH",    "isobaricInhPa"),
    "nuvem":         ("TCDC",  "isobaricInhPa"),
    "nuvemMistura":  ("CLWMR", "isobaricInhPa"),
    "u":             ("UGRD",  "isobaricInhPa"),
    "v":             ("VGRD",  "isobaricInhPa"),
    "o3":            ("O3MR",  "isobaricInhPa"),
    "total_o3":      ("TOZNE", "atmosphereSingleLayer"),
    "ps":            ("PRES",  "surface"),
    "temps":         ("TMP",   "surface"),
    "prnm":          ("PRMSL", "meanSea"),
    "uSupe":         ("UGRD",  "heightAboveGround"),
    "vSupe":         ("VGRD",  "heightAboveGround"),
    "precipRate":    ("PRATE", "surface"),
    "chuvaNaoConvec": ("APCP", "surface"),
    "categChuva":    ("CRAIN", "surface"),
}

def _build_filter_url(date_str: str, analysis: str, forecast: str,
                      var_code: str, level: int, region_code: str) -> str:
    """Build a NOAA filter_gfs URL that returns one variable/level for a region."""
    short_name, level_type = NOAA_FILTER_VARS[var_code]
    bounds = REGIOES[region_code]

    params = {
        "file": f"gfs.t{analysis}z.pgrb2.0p25.f{forecast:03d}",
        f"var_{short_name}": "on",
        "leftlon": bounds["lon_min"],
        "rightlon": bounds["lon_max"],
        "toplat": bounds["lat_max"],
        "bottomlat": bounds["lat_min"],
        "dir": f"/gfs.{date_str}/{analysis}/atmos",
    }
    if level_type == "isobaricInhPa":
        params[f"lev_{level}_mb"] = "on"
    elif level_type == "surface":
        params["lev_surface"] = "on"
    elif level_type == "meanSea":
        params["lev_mean_sea_level"] = "on"
    elif level_type == "heightAboveGround":
        params[f"lev_{level}_m_above_ground"] = "on"
    # atmosphereSingleLayer (e.g. Total ozone) needs no level selector.

    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{NOAA_FILTER_URL}?{qs}"


def fetch_filtered_grib(date_str: str, analysis: str, forecast: int,
                        var_code: str, level: int, region_code: str,
                        out_dir: Path = None) -> Path:
    """Download a single filtered GRIB file (region x variable x level)."""
    if var_code not in NOAA_FILTER_VARS:
        raise ValueError(f"Variable {var_code} not supported by NOAA filter endpoint")

    if out_dir is None:
        out_dir = GRIB_DIR / date_str / analysis
    out_dir.mkdir(parents=True, exist_ok=True)

    dest = out_dir / f"gfs.t{analysis}z.pgrb2.0p25.f{forecast:03d}_{var_code}_{region_code}_{level}.grb2"
    if dest.exists() and dest.stat().st_size > 0:
        logger.info(f"Already downloaded: {dest}")
        return dest

    url = _build_filter_url(date_str, analysis, forecast, var_code, level, region_code)
    logger.info("Fetching %s", url)
    with httpx.Client(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        if len(resp.content) < 100:
            raise RuntimeError(f"Empty/short payload for {url}")
        dest.write_bytes(resp.content)
    logger.info("Downloaded %s (%d bytes)", dest.name, dest.stat().st_size)
    return dest


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(download_gribs_main(date_arg))