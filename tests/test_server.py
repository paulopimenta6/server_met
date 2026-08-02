"""Testes da API REST (httpx ASGITransport, offline)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "4.0.0"
    assert "grib_files_available" in data


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MET Server" in response.text


@pytest.mark.asyncio
async def test_info_endpoint(client):
    response = await client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "4.0.0"
    assert "/docs" in data["docs"]


@pytest.mark.asyncio
async def test_static_assets(client):
    response = await client.get("/static/js/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    response = await client.get("/static/vendor/leaflet/leaflet.js")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_variables_endpoint(client):
    response = await client.get("/variables")
    assert response.status_code == 200
    keys = [v["key"] for v in response.json()["variables"]]
    assert "temp" in keys and "wind" in keys and "winds" in keys


@pytest.mark.asyncio
async def test_regions_endpoint(client):
    response = await client.get("/regions")
    assert response.status_code == 200
    names = [r["name"] for r in response.json()["regions"]]
    assert "SP" in names and "SA" in names


@pytest.mark.asyncio
async def test_catalog_endpoint(client):
    response = await client.get("/catalog")
    assert response.status_code == 200
    assert "entries" in response.json()


@pytest.mark.asyncio
async def test_gribs_list_endpoint(client):
    response = await client.get("/gribs/list")
    assert response.status_code == 200
    assert "gribs" in response.json()


@pytest.mark.asyncio
async def test_gribs_list_filtered_date(client):
    response = await client.get("/gribs/list?date=20990101")
    assert response.status_code == 200
    assert response.json() == {"gribs": [], "count": 0}


@pytest.mark.asyncio
async def test_grib_info_no_file(client):
    response = await client.post(
        "/gribs/info",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_grib_download_creates_task(client, isolated_db):
    response = await client.post("/gribs/download?date_str=20990101&analysis_hour=06")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "download_started"
    assert "task_id" in data

    status = await client.get(f"/gribs/download/{data['task_id']}")
    assert status.status_code == 200
    assert status.json()["task_type"] == "download"
    assert status.json()["status"] in ("pending", "running", "done", "failed")


@pytest.mark.asyncio
async def test_grib_download_status_missing(client):
    response = await client.get("/gribs/download/nao-existe")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_map_missing_grib(client):
    response = await client.post(
        "/maps/generate",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_animate_map_missing_grib(client):
    response = await client.post(
        "/maps/animate?duration_ms=500",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_scheduler_status(client):
    response = await client.get("/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert "grib_interval_min" in data


@pytest.mark.asyncio
async def test_generate_matrix_missing_grib(client):
    response = await client.post(
        "/matrices/generate",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_bluesky_wind_missing_grib(client):
    response = await client.post(
        "/bluesky/wind",
        json={"level": 500, "region": "SP", "date": "20990101"},
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_metar_stations(client):
    response = await client.get("/metar/stations")
    assert response.status_code == 200
    assert len(response.json()["stations"]) == 9


@pytest.mark.asyncio
async def test_metar_fetch_invalid_region(client):
    response = await client.post("/metar/fetch", json={"region": "SP", "icao_code": "ZZZZ"})
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_analysis_summary_missing_grib(client):
    response = await client.post(
        "/analysis/summary",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analysis_profile_missing_grib(client):
    response = await client.post(
        "/analysis/profile",
        json={"variable": "temp", "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analysis_timeseries_missing_grib(client):
    response = await client.post(
        "/analysis/timeseries",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analysis_charts_missing_grib(client):
    response = await client.post(
        "/analysis/charts",
        json={"variable": "temp", "level": 500, "region": "SP",
              "date": "20990101", "analysis": "06"},
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_analysis_region(client):
    response = await client.get("/analysis/regions/SP")
    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "SP"
    assert "bounds" in data


@pytest.mark.asyncio
async def test_db_status(client, isolated_db):
    response = await client.get("/db/status")
    assert response.status_code == 200
    data = response.json()
    assert set(data["tables"]) == {
        "downloads", "outputs", "metar_obs", "tasks", "analysis_results",
        "ingest_state",
    }


@pytest.mark.asyncio
async def test_history_downloads(client, isolated_db):
    response = await client.get("/history/downloads")
    assert response.status_code == 200
    assert "downloads" in response.json()


@pytest.mark.asyncio
async def test_history_outputs(client, isolated_db):
    response = await client.get("/history/outputs")
    assert response.status_code == 200
    assert "outputs" in response.json()


@pytest.mark.asyncio
async def test_history_analysis(client, isolated_db):
    response = await client.get("/history/analysis")
    assert response.status_code == 200
    assert "analysis" in response.json()


@pytest.mark.asyncio
async def test_files_traversal_blocked(client):
    response = await client.get("/files/mapas/../../etc/passwd")
    assert response.status_code in (400, 404)


@pytest.mark.asyncio
async def test_files_invalid_kind(client):
    response = await client.get("/files/segredo/x.png")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_files_missing(client):
    response = await client.get("/files/mapas/nao-existe.png")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_metar_history_empty(client, isolated_db):
    response = await client.get("/metar/history")
    assert response.status_code == 200
    assert response.json()["observations"] == []


@pytest.mark.asyncio
async def test_build_region_requires_selection(client):
    response = await client.post(
        "/maps/generate",
        json={"variable": "temp", "level": 500, "date": "20990101"},
    )
    assert response.status_code == 400
