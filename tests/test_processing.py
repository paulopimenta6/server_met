"""Testes de processamento: vento, extração de dados e METAR (offline)."""
import numpy as np

from server_MET.acquisition.metar_client import AERODROMOS, MetarClient
from server_MET.core.constants import NOAA_METAR_URL
from server_MET.processing.wind import WindProcessor


class TestWindProcessor:
    def test_compute_speed(self):
        wp = WindProcessor()
        u = np.array([3.0, 4.0])
        v = np.array([4.0, 3.0])
        assert np.allclose(wp.compute_speed(u, v), [5.0, 5.0])

    def test_compute_speed_knot(self):
        wp = WindProcessor()
        assert np.isclose(wp.compute_speed_knot(np.array([3.0]), np.array([4.0]))[0],
                          5.0 * 1.943844492)

    def test_compute_direction_met(self):
        wp = WindProcessor()
        assert np.isclose(wp.compute_direction_met(np.array([0.0]), np.array([-1.0]))[0], 0.0)

    def test_compute_direction_met_east(self):
        wp = WindProcessor()
        assert np.isclose(wp.compute_direction_met(np.array([-1.0]), np.array([0.0]))[0], 90.0)

    def test_pressure_to_altitude(self):
        wp = WindProcessor()
        assert np.isclose(wp.pressure_to_altitude(1013.25), 0.0, atol=0.1)

    def test_pressure_to_altitude_500(self):
        wp = WindProcessor()
        alt = wp.pressure_to_altitude(500.0)
        assert 18000 < alt < 19000

    def test_near_surface_levels(self):
        wp = WindProcessor()
        assert wp.get_near_surface_levels() == [20, 30, 40, 50, 80]


class TestMetarClient:
    def test_aerodromos(self):
        assert "SP" in AERODROMOS
        assert AERODROMOS["SP"] == "SBGR"
        assert len(AERODROMOS) == 9

    def test_metar_url(self):
        assert "aviationweather.gov" in NOAA_METAR_URL
        assert "api/data/metar" in NOAA_METAR_URL
        assert "format=json" in NOAA_METAR_URL

    def test_extract_raw_text_from_json(self):
        client = MetarClient()
        data = [{"icaoId": "SBGR", "rawOb": "METAR SBGR 010900Z 36003KT CAVOK 15/10 Q1020"}]
        assert client.extract_raw_text_from_json(data) == "METAR SBGR 010900Z 36003KT CAVOK 15/10 Q1020"
        assert client.extract_raw_text_from_json([]) is None

    def test_parse_local_metar(self, isolated_db):
        client = MetarClient()
        raw = "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020="
        parsed = client.get_parsed_metar("SBPA", raw)
        assert parsed is not None
        assert parsed["station_code"] == "SBPA"
        assert parsed["wind"]["direction"] == 120
        assert parsed["wind"]["speed"] == 5
        assert parsed["temperatures"]["temperature"] == 18
        assert parsed["qnh"] == 1020

    def test_parse_vrb_wind_metar(self, isolated_db):
        client = MetarClient()
        raw = "METAR SBGL 212200Z VRB03KT CAVOK 22/15 Q1015="
        parsed = client.get_parsed_metar("SBGL", raw)
        assert parsed is not None
        assert parsed["wind"]["direction"] == "VRB"
        assert parsed["wind"]["speed"] == 3
