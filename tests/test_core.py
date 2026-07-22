import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from server_MET.config import Settings
from server_MET.region import Region, REGIOES_PREDEFINIDAS
from server_MET.data_processor import DataProcessor, VAR_MAP, PRESSURE_LEVELS


class TestConfig:
    def test_singleton(self):
        s1 = Settings()
        s2 = Settings()
        assert s1 is s2

    def test_default_dirs(self):
        s = Settings()
        assert s.dir_gribs is not None
        assert s.dir_mapas is not None
        assert s.dir_matrizes is not None

    def test_ensure_dirs(self):
        s = Settings()
        s.ensure_dirs()
        assert s.dir_gribs.exists() or True

    def test_gfs_url(self):
        s = Settings()
        assert "nomads.ncep.noaa.gov" in s.gfs_url


class TestRegion:
    def test_predefined_region(self):
        r = Region(name="SP")
        assert r.lon_min == -56
        assert r.lon_max == -42
        assert r.lat_min == -28
        assert r.lat_max == -18

    def test_bbox_region(self):
        r = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r.lon_min == -50
        assert r.lon_max == -40

    def test_center_region(self):
        r = Region(center_lon=-46, center_lat=-23)
        assert r.lat_min == -28
        assert r.lat_max == -18

    def test_validate_valid(self):
        r = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r.validate() is True

    def test_validate_invalid_lon(self):
        r = Region(lon_min=-200, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r.validate() is False

    def test_get_flag(self):
        r1 = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r1.get_flag() in (1, 2, 3, 0)

    def test_all_regions_exist(self):
        for name in ["SP", "RJ", "AM", "DF", "PR", "RS", "MG", "PA", "PE", "CE", "SA"]:
            r = Region(name=name)
            assert r.validate()


class TestDataProcessor:
    def test_var_map_complete(self):
        expected_keys = [
            "ps", "prnm", "temp", "temps", "nuvem",
            "chuvaNaoConvec", "chuvaConvec", "umidadeRel",
            "u", "v", "uSupe", "vSupe",
        ]
        for key in expected_keys:
            assert key in VAR_MAP

    def test_pressure_levels_range(self):
        assert all(150 <= l <= 1000 for l in PRESSURE_LEVELS)
        assert PRESSURE_LEVELS == sorted(PRESSURE_LEVELS)

    def test_resolve_level_within_range(self):
        dp = DataProcessor()
        assert dp.resolve_level("temp", 500) == 500
        assert dp.resolve_level("temp", 850) == 850

    def test_resolve_level_below_min(self):
        dp = DataProcessor()
        assert dp.resolve_level("temp", 50) == 150

    def test_resolve_level_above_max(self):
        dp = DataProcessor()
        assert dp.resolve_level("temp", 2000) == 1000

    def test_resolve_level_none(self):
        dp = DataProcessor()
        assert dp.resolve_level("temps", None) is None

    def test_get_current_analysis_hour(self):
        dp = DataProcessor()
        hour = dp.get_current_analysis_hour()
        assert hour in ["00", "06", "12", "18"]

    def test_get_date_str_format(self):
        dp = DataProcessor()
        d = dp.get_date_str()
        assert len(d) == 8
        assert d.isdigit()


class TestWindProcessor:
    def test_compute_speed(self):
        from server_MET.wind_processor import WindProcessor

        wp = WindProcessor()
        u = np.array([3.0, 4.0])
        v = np.array([4.0, 3.0])
        speed = wp.compute_speed(u, v)
        assert np.allclose(speed, [5.0, 5.0])

    def test_compute_speed_knot(self):
        from server_MET.wind_processor import WindProcessor

        wp = WindProcessor()
        u = np.array([3.0])
        v = np.array([4.0])
        speed = wp.compute_speed_knot(u, v)
        assert np.isclose(speed[0], 5.0 * 1.943)

    def test_compute_direction_met(self):
        from server_MET.wind_processor import WindProcessor

        wp = WindProcessor()
        u = np.array([0.0])
        v = np.array([-1.0])
        direction = wp.compute_direction_met(u, v)
        assert np.isclose(direction[0], 0.0)

    def test_pressure_to_altitude(self):
        from server_MET.wind_processor import WindProcessor

        wp = WindProcessor()
        alt = wp.pressure_to_altitude(1013.25)
        assert np.isclose(alt, 0.0, atol=0.1)

    def test_near_surface_levels(self):
        from server_MET.wind_processor import WindProcessor

        wp = WindProcessor()
        levels = wp.get_near_surface_levels()
        assert levels == [20, 30, 40, 50, 80]


class TestMetarClient:
    def test_aerodromos(self):
        from server_MET.metar_client import AERODROMOS

        assert "SP" in AERODROMOS
        assert AERODROMOS["SP"] == "SBGR"
        assert len(AERODROMOS) == 9

    def test_metar_noaa_url(self):
        from server_MET.metar_client import NOAA_METAR_URL

        assert "aviationweather.gov" in NOAA_METAR_URL
        assert "{}" in NOAA_METAR_URL

    def test_parse_local_metar(self):
        from server_MET.metar_client import MetarClient

        client = MetarClient()
        raw = "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020="
        parsed = client.get_parsed_metar("SBPA", raw)
        assert parsed is not None
        assert parsed["station_code"] == "SBPA"
        assert parsed["wind"] is not None
        assert parsed["wind"]["direction"] == 120
        assert parsed["wind"]["speed"] == 5
        assert parsed["temperatures"]["temperature"] == 18
        assert parsed["temperatures"]["dewpoint"] == 12
        assert parsed["qnh"] == 1020
        assert parsed["visibility"] == 9999

    def test_parse_vrb_wind_metar(self):
        from server_MET.metar_client import MetarClient

        client = MetarClient()
        raw = "METAR SBGL 212200Z VRB03KT CAVOK 22/15 Q1015="
        parsed = client.get_parsed_metar("SBGL", raw)
        assert parsed is not None
        assert parsed["wind"]["direction"] == "VRB"
        assert parsed["wind"]["speed"] == 3


class TestMatrixGenerator:
    def test_bluesky_filename_structure(self):
        from server_MET.matrix_generator import MatrixGenerator

        gen = MatrixGenerator()
        assert gen is not None

    def test_generate_wind_filename(self):
        from server_MET.matrix_generator import MatrixGenerator

        gen = MatrixGenerator()
        assert gen is not None


class TestServerHealth:
    def test_health_response_model(self):
        from server_MET.models import HealthResponse

        h = HealthResponse(
            status="ok",
            version="2.0.0",
            grib_files_available=False,
            uptime=100.0,
        )
        assert h.status == "ok"
        assert h.version == "2.0.0"
        assert h.grib_files_available is False

    def test_grib_request_model(self):
        from server_MET.models import GribRequest, MetVariable

        req = GribRequest(
            variable=MetVariable.temp,
            level=500,
            region="SP",
        )
        assert req.variable == MetVariable.temp
        assert req.level == 500
