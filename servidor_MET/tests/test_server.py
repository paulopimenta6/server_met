import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import tempfile
import json

from server_MET.server import app
from server_MET.config import Settings


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "grib_files_available" in data


@pytest.mark.asyncio
async def test_variables_endpoint(client):
    response = await client.get("/variables")
    assert response.status_code == 200
    data = response.json()
    assert "variables" in data
    assert len(data["variables"]) > 0


@pytest.mark.asyncio
async def test_regions_endpoint(client):
    response = await client.get("/regions")
    assert response.status_code == 200
    data = response.json()
    assert "regions" in data
    region_names = [r["name"] for r in data["regions"]]
    assert "SP" in region_names
    assert "RJ" in region_names
    assert "SA" in region_names


@pytest.mark.asyncio
async def test_gribs_list_endpoint(client):
    response = await client.get("/gribs/list")
    assert response.status_code == 200
    data = response.json()
    assert "gribs" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_metar_stations(client):
    response = await client.get("/metar/stations")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert data["stations"]["SP"] == "SBGR"


@pytest.mark.asyncio
async def test_grib_info_no_file(client):
    response = await client.post(
        "/gribs/info",
        json={"variable": "temp", "level": 500, "region": "SP", "date": "20000101"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_map_missing_grib(client):
    response = await client.post(
        "/maps/generate",
        json={
            "variable": "temp",
            "level": 500,
            "region": "SP",
            "date": "20000101",
            "analysis": "00",
        },
    )
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_generate_matrix_missing_grib(client):
    response = await client.post(
        "/matrices/generate",
        json={
            "variable": "temp",
            "level": 500,
            "region": "SP",
            "date": "20000101",
            "analysis": "00",
        },
    )
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_metar_fetch_invalid(client):
    response = await client.post(
        "/metar/fetch", json={"icao_code": "XXXX"}
    )
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_metar_fetch_by_region(client):
    response = await client.post(
        "/metar/fetch", json={"region": "SP"}
    )
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_bluesky_wind_missing_grib(client):
    response = await client.post(
        "/bluesky/wind",
        json={
            "level": 500,
            "region": "SP",
            "date": "20000101",
        },
    )
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_cleanup_endpoint(client):
    response = await client.post("/cleanup?days_old=30")
    assert response.status_code == 200
    data = response.json()
    assert "removed_files" in data


@pytest.mark.asyncio
async def test_health_response_model():
    from server_MET.models import HealthResponse

    h = HealthResponse(
        status="ok",
        version="2.0.0",
        grib_files_available=False,
        uptime=0.0,
    )
    assert h.model_dump()["status"] == "ok"
