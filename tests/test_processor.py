#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for core.processor (derived wind resultant computation).
No network / database required: PYTHONPATH=. pytest tests/test_processor.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.grib_reader import GribReader  # noqa: E402
from core.processor import DataProcessor  # noqa: E402


def _fake_extracted(values, level=850):
    return {
        "data": np.asarray(values, dtype=float),
        "level_type": "isobaricInhPa",
        "level": level,
        "lats": np.array([-20.0, -21.0]),
        "lons": np.array([-45.0, -46.0]),
        "metadata": {"forecastTime": 6, "dataDate": 20260807, "validDate": 20260807},
    }


def test_wind_resultant_pythagoras():
    processor = DataProcessor(GribReader(Path("/nonexistent")))
    u = _fake_extracted([3.0, 4.0])
    v = _fake_extracted([4.0, 0.0])
    out = processor.combine_wind_resultant(u, v, var_code="vento",
                                           name="Wind speed", unit="m/s")
    np.testing.assert_allclose(out["data"], [5.0, 4.0])
    assert out["variable_code"] == "vento"
    assert out["unit"] == "m/s"
    assert out["level_type"] == "isobaricInhPa"
    assert out["level"] == 850


def test_wind_resultant_nonnegative():
    processor = DataProcessor(GribReader(Path("/nonexistent")))
    rng = np.random.default_rng(42)
    u = _fake_extracted(rng.normal(size=100))
    v = _fake_extracted(rng.normal(size=100))
    out = processor.combine_wind_resultant(u, v)
    assert np.all(out["data"] >= 0)
    np.testing.assert_allclose(out["data"], np.sqrt(u["data"] ** 2 + v["data"] ** 2))


def test_wind_resultant_requires_both_components():
    processor = DataProcessor(GribReader(Path("/nonexistent")))
    assert processor.combine_wind_resultant(None, _fake_extracted([1.0])) is None
    empty = _fake_extracted(np.array([]))
    assert processor.combine_wind_resultant(empty, _fake_extracted([1.0])) is None


class _FakeMessage:
    level = 850
    forecastTime = 6
    dataDate = 20260807
    validDate = 20260807
    analDate = 20260807

    def data(self, lat1=None, lat2=None, lon1=None, lon2=None):
        return np.array([[1.0]]), np.array([[-20.0]]), np.array([[-45.0]])

    @property
    def values(self):
        return np.array([[1.0]])

    def latlons(self):
        return np.array([[-20.0]]), np.array([[-45.0]])


class _FakeReader:
    def __init__(self):
        self.calls = []

    def select_messages(self, file_path, name=None, level_type=None, level=None):
        self.calls.append({"name": name, "level_type": level_type, "level": level})
        return [_FakeMessage()]


def test_extract_level_meaningful_passes_level():
    reader = _FakeReader()
    out = DataProcessor(reader).extract_variable("/x.grb2", "temp", level=850)
    assert reader.calls[-1]["level"] == 850
    assert out is not None
    assert out["level_type"] == "isobaricInhPa"


@pytest.mark.parametrize("var_code", ["tempSolo", "umidadeSolo", "total_o3", "cisalhamentoVertical"])
def test_extract_level_not_meaningful_ignores_level(var_code):
    reader = _FakeReader()
    out = DataProcessor(reader).extract_variable("/x.grb2", var_code, level=0)
    assert reader.calls[-1]["level"] is None
    assert out is not None


def test_extract_unknown_variable_returns_none():
    reader = _FakeReader()
    out = DataProcessor(reader).extract_variable("/x.grb2", "naoExiste", level=0)
    assert out is None
    assert reader.calls == []
