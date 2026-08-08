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


def _latest_date(client) -> str:
    """Most recent date with processed GFS data (avoids hardcoded dates)."""
    r = client.get(f"{API}/data/available")
    assert r.status_code == 200
    dates = r.json().get("dates", [])
    assert dates, "no processed dates in the database (run the pipeline first)"
    return dates[0]


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
    assert len(vars) == 47  # 26 originais + 20 novas + 1 catalog-only (aguaLiquidaSolo)
    categories = {v["category"] for v in vars}
    assert "pollution" in categories
    assert "temperature" in categories
    assert "convection" in categories
    assert "radar" in categories
    assert "soil" in categories
    assert "dynamics" in categories


def test_document_ml_variables(client):
    # Conjunto recomendado para Machine Learning no documento de análise
    # (analise_variaveis_meteorologicas_grib_025.txt), mapeado para o GFS.
    r = client.get(f"{API}/data/variables")
    assert r.status_code == 200
    by_code = {v["code"]: v for v in r.json()["variables"]}

    expected_available = {
        # Termodinâmica
        "prnm", "temp", "umidadeRel", "umidadeEsp", "alturaGeo",
        # Vento
        "u", "v", "ventoRajada",
        # Nuvens
        "nuvem",
        # Hidrometeoros
        "chuvaRazao", "geloRazao", "neveRazao", "granizoRazao",
        # Convecção
        "cape", "cin",
        # Radar
        "reflectividade",
        # Solo
        "umidadeSolo", "tempSolo",
        # Dinâmica
        "velVertical", "vorticidade",
    }
    for code in expected_available:
        assert code in by_code, f"variável {code} ausente do catálogo"
        assert by_code[code]["available"] is True, f"{code} deveria estar disponível"

    # Agrupamentos do documento também mapeados
    extra = {
        "reflectividadeMax", "visibilidade", "cisalhamentoVertical",
        "velVerticalGeo", "umidadePrecipitavel", "indiceLift", "ventoSup", "nuvemMistura",
    }
    for code in extra:
        assert by_code[code]["available"] is True, f"{code} deveria estar disponível"

    # Água líquida do solo não é exposta pelo filtro NOAA (catalog-only)
    assert by_code["aguaLiquidaSolo"]["available"] is False
    assert by_code["aguaLiquidaSolo"]["category"] == "soil"


def test_new_variables(client):
    # New variables added in v2.1: wind resultant (vento/ventoSup), rain
    # (precipRate, categChuva, chuvaNaoConvec) and cloud (nuvemMistura).
    r = client.get(f"{API}/data/variables")
    assert r.status_code == 200
    by_code = {v["code"]: v for v in r.json()["variables"]}

    assert "vento" in by_code and by_code["vento"]["available"] is True
    assert "ventoSup" in by_code and by_code["ventoSup"]["available"] is True
    assert "precipRate" in by_code and by_code["precipRate"]["available"] is True
    assert "categChuva" in by_code and by_code["categChuva"]["available"] is True
    assert "chuvaNaoConvec" in by_code and by_code["chuvaNaoConvec"]["available"] is True
    assert "nuvemMistura" in by_code and by_code["nuvemMistura"]["available"] is True

    assert by_code["vento"]["category"] == "wind"
    assert by_code["vento"]["unit"] == "m/s"
    assert by_code["precipRate"]["category"] == "precipitation"
    assert by_code["precipRate"]["unit"] == "mm/h"
    assert by_code["nuvemMistura"]["category"] == "cloud"


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


def test_all_analyses_and_forecasts(client):
    # The pipeline must download and process GFS data for every analysis
    # cycle (00/06/12/18) combined with every forecast hour (f000/f006/f012/f018).
    r = client.get(f"{API}/data/available")
    assert r.status_code == 200
    body = r.json()
    assert set(body["analyses"]) == {"00", "06", "12", "18"}
    assert set(body["forecasts"]) == {0, 6, 12, 18}

    # Every analysis x forecast combination must have at least one record.
    for analysis in body["analyses"]:
        for forecast in body["forecasts"]:
            q = client.get(f"{API}/data/",
                           params={"variable": "temp", "region": "SP",
                                   "level": 1000, "analysis": analysis,
                                   "forecast": forecast})
            assert q.status_code == 200, f"falha em {analysis}Z f{forecast:03d}"
            assert q.json()["total"] > 0, f"sem dados em {analysis}Z f{forecast:03d}"


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
                   params={"date": _latest_date(client), "analysis": "00"})
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
                   params={"level": 850, "date": _latest_date(client), "analysis": "00"})
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


def test_wind_resultant_data(client):
    r = client.get(f"{API}/data/", params={"variable": "vento", "region": "SP", "level": 850})
    assert r.status_code == 200
    assert r.json()["total"] > 0
    rec = r.json()["data"][0]
    assert rec["variable_code"] == "vento"
    assert rec["max_value"] > 0  # wind magnitude is always non-negative
    assert rec["min_value"] >= 0


def test_wind_resultant_map(client):
    r = client.get(f"{API}/maps/vento/SP", params={"level": 850})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_rain_and_cloud_data(client):
    r = client.get(f"{API}/data/", params={"variable": "precipRate", "region": "SP"})
    assert r.status_code == 200
    assert r.json()["total"] > 0
    r2 = client.get(f"{API}/data/", params={"variable": "nuvemMistura", "region": "SP", "level": 850})
    assert r2.status_code == 200
    assert r2.json()["total"] > 0


# --------------------------------------------------------------------------- #
# v2.1 - variáveis do documento analise_variaveis_meteorologicas_grib_025.txt
# --------------------------------------------------------------------------- #
_DOC_ISOBARIC_850 = [
    "umidadeEsp", "alturaGeo", "vorticidade", "velVertical",
    "velVerticalGeo", "chuvaRazao", "geloRazao", "neveRazao", "granizoRazao",
]
_DOC_SURFACE = [
    "cape", "cin", "indiceLift", "reflectividade", "reflectividadeMax",
    "visibilidade", "tempSolo", "umidadeSolo", "umidadePrecipitavel",
    "ventoRajada", "cisalhamentoVertical",
]


@pytest.mark.parametrize("var", _DOC_ISOBARIC_850)
def test_doc_isobaric_850_data(client, var):
    r = client.get(f"{API}/data/", params={"variable": var, "region": "SP", "level": 850})
    assert r.status_code == 200
    assert r.json()["total"] > 0, f"sem dados para {var} em 850 hPa"


@pytest.mark.parametrize("var", _DOC_SURFACE)
def test_doc_surface_data(client, var):
    r = client.get(f"{API}/data/", params={"variable": var, "region": "SP"})
    assert r.status_code == 200
    assert r.json()["total"] > 0, f"sem dados para {var}"


def test_doc_convection_units(client):
    r = client.get(f"{API}/data/", params={"variable": "cape", "region": "SP"})
    rec = r.json()["data"][0]
    assert rec["variable_code"] == "cape"
    r2 = client.get(f"{API}/data/", params={"variable": "cin", "region": "SP"})
    assert r2.json()["total"] > 0


def test_doc_radar_map(client):
    r = client.get(f"{API}/maps/reflectividade/SP",
                   params={"date": _latest_date(client), "analysis": "00"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_doc_soil_map(client):
    r = client.get(f"{API}/maps/tempSolo/SP",
                   params={"date": _latest_date(client), "analysis": "00"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")


def test_doc_humidity_map(client):
    r = client.get(f"{API}/maps/umidadeEsp/SP",
                   params={"level": 850, "date": _latest_date(client), "analysis": "00"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")