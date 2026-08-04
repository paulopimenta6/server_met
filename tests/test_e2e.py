#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end tests with real data for Server MET v2.0.

Uses FastAPI's in-process TestClient, so no external server is required:
    PYTHONPATH=. pytest tests/test_e2e.py -v
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402

API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_variables(client):
    r = client.get(f"{API}/data/variables")
    assert r.status_code == 200
    vars = r.json()["variables"]
    assert len(vars) == 21
    categories = {v["category"] for v in vars}
    assert "pollution" in categories
    assert "temperature" in categories


def test_regions(client):
    r = client.get(f"{API}/data/regions")
    assert r.status_code == 200
    assert len(r.json()["regions"]) == 18


def test_dashboard(client):
    r = client.get(f"{API}/data/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_records"] > 0
    assert data["metar"]["reports"] > 0


def test_data_query(client):
    r = client.get(f"{API}/data/", params={"variable": "temp", "region": "SP", "level": 1000})
    assert r.status_code == 200
    assert r.json()["total"] > 0
    rec = r.json()["data"][0]
    assert rec["min_value"] < rec["max_value"]


def test_map_png(client):
    r = client.get(f"{API}/maps/temp/SP", params={"level": 1000})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_map_surface(client):
    r = client.get(f"{API}/maps/ps/SP")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_data_surface(client):
    r = client.get(f"{API}/data/", params={"variable": "ps", "region": "SP"})
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_metar_stations(client):
    r = client.get(f"{API}/metar/stations")
    assert r.status_code == 200
    assert len(r.json()["stations"]) > 0


def test_metar_latest(client):
    r = client.get(f"{API}/metar/SBGR")
    assert r.status_code == 200
    body = r.json()
    assert body["metar"]
    assert body["decoded"]


def test_metar_all(client):
    r = client.get(f"{API}/metar/latest/all")
    assert r.status_code == 200
    assert len(r.json()["metars"]) > 0


def test_metar_station_name_fixed(client):
    # Guarulhos (SBGR) is in SP; AviationWeather upstream sends "PR" in the
    # name, which must be corrected to "SP".
    r = client.get(f"{API}/metar/stations")
    sbgr = next(s for s in r.json()["stations"] if s["code"] == "SBGR")
    assert sbgr["state"] == "SP"
    assert "PR, BR" not in sbgr["name"]
    assert "SP, BR" in sbgr["name"]


def test_total_ozone_variable(client):
    r = client.get(f"{API}/data/variables")
    vars_ = r.json()["variables"]
    total_o3 = next((v for v in vars_ if v["code"] == "total_o3"), None)
    assert total_o3 is not None
    assert total_o3["category"] == "pollution"
    assert total_o3["unit"] == "DU"


def test_pollution_available_from_varmet(client):
    # Only Ozone mixing ratio (o3) and Total ozone (total_o3) exist in the GFS
    # pgrb2 0p25 inventory (varMET). Everything else stays catalogued but marked
    # unavailable so the frontend does not offer it.
    r = client.get(f"{API}/data/variables")
    pollution = [v for v in r.json()["variables"] if v["category"] == "pollution"]
    available = {v["code"] for v in pollution if v["available"]}
    assert available == {"o3", "total_o3"}
    assert {v["code"] for v in pollution} >= {"no2", "so2", "co", "pm25", "pm10", "aod", "dust"}


def test_map_total_ozone(client):
    r = client.get(f"{API}/maps/total_o3/SP",
                   params={"date": "20260804", "analysis": "00"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_frontend(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Server MET" in r.text
    # index.html must reference assets through the /static mount (root paths 404)
    assert 'href="static/style.css"' in r.text
    assert 'src="static/app.js"' in r.text
    assert 'href="style.css"' not in r.text
    assert 'src="app.js"' not in r.text


def test_frontend_assets(client):
    r_css = client.get("/static/style.css")
    assert r_css.status_code == 200
    assert "text/css" in r_css.headers["content-type"]
    r_js = client.get("/static/app.js")
    assert r_js.status_code == 200
    assert "text/javascript" in r_js.headers["content-type"]


def test_map_with_date_and_analysis(client):
    # The frontend always requests maps with date+analysis together; this must
    # not 404 even though the filename embeds analysis before date.
    r = client.get(f"{API}/maps/temp/SP",
                   params={"level": 850, "date": "20260804", "analysis": "00"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_export_csv(client):
    r = client.get(f"{API}/data/export/csv",
                   params={"variable": "temp", "region": "SP", "level": 1000})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]


def test_export_csv_surface(client):
    r = client.get(f"{API}/data/export/csv",
                   params={"variable": "ps", "region": "SP"})
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]