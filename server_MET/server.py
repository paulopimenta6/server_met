import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server_MET.config import Settings
from server_MET.grib_downloader import GribDownloader
from server_MET.grib_reader import GribReader
from server_MET.data_processor import DataProcessor
from server_MET.map_generator import MapGenerator
from server_MET.matrix_generator import MatrixGenerator
from server_MET.region import Region
from server_MET.metar_client import MetarClient, AERODROMOS
from server_MET.data_processor import VAR_MAP as DP_VAR_MAP
from server_MET.models import (
    GribRequest,
    MetarRequest,
    MapRequest,
    WindRequest,
    HealthResponse,
    MetVariable,
    RegionName,
    OutputFormat,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = Settings()
settings.ensure_dirs()

app = FastAPI(
    title="MET Server - GFS Weather Data Server",
    description="Download, process, map and serve meteorological data from NOAA GFS model",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()

grib_reader = GribReader()
grib_downloader = GribDownloader()
data_processor = DataProcessor()
map_generator = MapGenerator()
matrix_generator = MatrixGenerator()
metar_client = MetarClient()

TEMP_DIR = Path("/tmp/opencode/servidor_MET")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _build_region(grib_req) -> Region:
    if grib_req.region:
        return Region(name=grib_req.region.value)
    if all(
        getattr(grib_req, attr) is not None
        for attr in ["lon_min", "lon_max", "lat_min", "lat_max"]
    ):
        return Region(
            lon_min=grib_req.lon_min,
            lon_max=grib_req.lon_max,
            lat_min=grib_req.lat_min,
            lat_max=grib_req.lat_max,
        )
    if grib_req.lon is not None and grib_req.lat is not None:
        return Region(center_lon=grib_req.lon, center_lat=grib_req.lat)
    raise HTTPException(
        status_code=400,
        detail="Provide 'region', bounding box (lon_min/lon_max/lat_min/lat_max), or center (lon/lat)",
    )


def _get_level_str(level) -> str:
    if level is None or level == "surface":
        return "surface"
    return str(level)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    grib_dirs = list(settings.dir_gribs.rglob("*.grb2"))
    return HealthResponse(
        status="ok",
        version="2.0.0",
        grib_files_available=len(grib_dirs) > 0,
        uptime=time.time() - START_TIME,
    )


@app.get("/variables")
async def list_variables():
    return {
        "variables": [
            {"key": k, "name": v[0], "level_type": v[1]}
            for k, v in DP_VAR_MAP.items()
        ]
    }


@app.get("/regions")
async def list_regions():
    from server_MET.region import REGIOES_PREDEFINIDAS

    return {
        "regions": [
            {"name": k, "bounds": v} for k, v in REGIOES_PREDEFINIDAS.items()
        ]
    }


@app.get("/gribs/list")
async def list_grib_files(date: Optional[str] = None):
    base = settings.dir_gribs
    if date:
        base = base / date
    if not base.exists():
        return {"gribs": []}
    files = []
    for f in base.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            files.append(str(f.relative_to(settings.dir_gribs)))
    return {"gribs": files, "count": len(files)}


@app.post("/gribs/download")
async def download_gribs(
    background_tasks: BackgroundTasks,
    date_str: Optional[str] = None,
    analysis_hour: Optional[str] = None,
):
    def _download():
        grib_downloader.download_gribs_all_resolutions(
            date_str=date_str, analysis_hour=analysis_hour
        )

    background_tasks.add_task(_download)
    return {"status": "download_started", "date": date_str, "analysis": analysis_hour}


@app.post("/gribs/info")
async def grib_info(request: GribRequest):
    date_str = request.date or data_processor.get_date_str()
    ana = request.analysis or data_processor.get_current_analysis_hour()
    prev = request.forecast or "00"
    f = grib_reader.find_grib_file(date_str, ana, prev)
    if f is None:
        raise HTTPException(status_code=404, detail="GRIB file not found")
    vars_list = grib_reader.list_variables(f)
    return {"file": str(f), "variables": vars_list, "count": len(vars_list)}


@app.post("/maps/generate")
async def generate_map(request: MapRequest):
    region = _build_region(request)
    date_str = request.date or data_processor.get_date_str()
    ana = request.analysis or data_processor.get_current_analysis_hour()
    output_dir = str(TEMP_DIR / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    files = map_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        output_dir=output_dir,
    )
    if not files:
        raise HTTPException(status_code=500, detail="Map generation failed")
    return {"maps": files, "count": len(files)}


@app.post("/matrices/generate")
async def generate_matrix(request: GribRequest):
    region = _build_region(request)
    date_str = request.date or data_processor.get_date_str()
    ana = request.analysis or data_processor.get_current_analysis_hour()
    output_dir = str(TEMP_DIR / uuid.uuid4().hex)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    files = matrix_generator.generate(
        var_name=request.variable.value,
        region=region,
        level=request.level,
        date_str=date_str,
        analysis=ana,
        output_dir=output_dir,
    )
    if not files:
        raise HTTPException(status_code=500, detail="Matrix generation failed")
    return {"matrices": files, "count": len(files)}


@app.post("/metar/fetch")
async def fetch_metar(request: MetarRequest):
    if request.region:
        region_name = request.region.value
        result = metar_client.get_metar_for_region(region_name)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"METAR not available for {region_name}"
            )
        return result
    if request.icao_code:
        data = metar_client.get_metar(request.icao_code)
        if data is None:
            raise HTTPException(
                status_code=404, detail=f"METAR not available for {request.icao_code}"
            )
        return data
    raise HTTPException(status_code=400, detail="Provide 'region' or 'icao_code'")


@app.get("/metar/all")
async def get_all_metars():
    results = metar_client.get_all_metars()
    return {"metars": results, "count": len(results)}


@app.get("/metar/stations")
async def list_metar_stations():
    return {"stations": AERODROMOS}


@app.post("/bluesky/wind")
async def generate_bluesky_wind(request: WindRequest):
    region = _build_region(request)
    result = matrix_generator.generate_bluesky(
        region=region,
        level=request.level,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="Bluesky wind generation failed")
    return {"file": result}


@app.post("/cleanup")
async def cleanup_old_data(days_old: int = 2):
    removed = grib_downloader.clean_old_gribs(days_old=days_old)
    return {"removed_files": removed, "days_old": days_old}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server_MET.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
