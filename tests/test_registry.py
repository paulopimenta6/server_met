#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the variable registry + NOAA filter URL mapping introduced
for the document analise_variaveis_meteorologicas_grib_025.txt.
No network required: PYTHONPATH=. pytest tests/test_registry.py -v
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.variables import (  # noqa: E402
    VARIABLES_MET, AVAILABLE_IN_GFS, VARIABLE_CATEGORIES,
    is_variable_available, level_is_meaningful, convert_value,
)
from core.downloader import NOAA_FILTER_VARS, _build_filter_url  # noqa: E402


def _categories_of(code):
    return [cat for cat, codes in VARIABLE_CATEGORIES.items() if code in codes]


def test_all_available_have_filter_entry():
    # Every non-derived available variable must be downloadable via the filter.
    derived = {"vento", "ventoSup"}
    missing = sorted(AVAILABLE_IN_GFS - set(NOAA_FILTER_VARS) - derived)
    assert missing == []


def test_every_available_in_one_category():
    for code in AVAILABLE_IN_GFS:
        cats = _categories_of(code)
        assert len(cats) == 1, f"{code} deve estar em exatamente 1 categoria ({cats})"


def test_document_variables_mapped():
    expected = {
        "umidadeEsp", "alturaGeo", "ventoRajada", "cisalhamentoVertical",
        "chuvaRazao", "geloRazao", "neveRazao", "granizoRazao",
        "cape", "cin", "indiceLift", "reflectividade", "reflectividadeMax",
        "visibilidade", "tempSolo", "umidadeSolo",
        "vorticidade", "velVertical", "velVerticalGeo", "umidadePrecipitavel",
    }
    assert expected <= AVAILABLE_IN_GFS
    for code in expected:
        assert is_variable_available(code)


def test_liquid_soil_catalog_only():
    assert "aguaLiquidaSolo" in VARIABLES_MET
    assert not is_variable_available("aguaLiquidaSolo")
    assert VARIABLES_MET["aguaLiquidaSolo"]["experimental"] is True


def test_level_meaningfulness():
    assert level_is_meaningful("isobaricInhPa")
    assert level_is_meaningful("surface")
    assert level_is_meaningful("heightAboveGround")
    assert not level_is_meaningful("atmosphere")
    assert not level_is_meaningful("atmosphereSingleLayer")
    assert not level_is_meaningful("hybrid")
    assert not level_is_meaningful("tropopause")
    assert not level_is_meaningful("depthBelowLandLayer")


def test_conversions():
    assert convert_value("visibilidade", 10_000) == 10.0      # m -> km
    assert convert_value("umidadeEsp", 0.014) == 14.0          # kg/kg -> g/kg
    assert convert_value("tempSolo", 300.15) == pytest.approx(27.0)
    assert convert_value("umidadePrecipitavel", 25.0) == 25.0  # kg/m2 -> mm


def test_filter_url_isobaric():
    url = _build_filter_url("20260807", "00", 6, "umidadeEsp", 850, "FOR")
    assert "var_SPFH=on" in url
    assert "lev_850_mb=on" in url


def test_filter_url_surface():
    url = _build_filter_url("20260807", "00", 6, "cape", 0, "FOR")
    assert "var_CAPE=on" in url
    assert "lev_surface=on" in url


def test_filter_url_no_level_selector():
    for code in ["reflectividade", "reflectividadeMax", "umidadePrecipitavel", "cisalhamentoVertical"]:
        url = _build_filter_url("20260807", "00", 6, code, 0, "FOR")
        assert "lev_" not in url, code


def test_filter_url_soil():
    url = _build_filter_url("20260807", "00", 6, "tempSolo", 0, "FOR")
    assert "var_TSOIL=on" in url
    assert "lev_0-0.1_m_below_ground=on" in url
