"""Testes da camada core: configuração, constantes, regiões e modelos."""
import numpy as np
import pytest
from pydantic import ValidationError

from server_MET.core.config import Settings
from server_MET.core.constants import PRESSURE_LEVELS, UNITS_MAP, VAR_MAP
from server_MET.core.models import GribRequest, MapRequest, MetVariable, RegionName
from server_MET.processing.processor import DataProcessor
from server_MET.processing.regions import REGIOES_PREDEFINIDAS, Region, regioes_predefinidas


class TestSettings:
    def test_singleton(self):
        s1 = Settings()
        s2 = Settings()
        assert s1 is s2

    def test_default_dirs(self):
        s = Settings()
        assert s.dir_gribs is not None
        assert s.dir_mapas is not None
        assert s.dir_matrizes is not None
        assert s.dir_analise is not None
        assert s.dir_tmp is not None

    def test_db_path(self):
        s = Settings()
        assert str(s.db_path).endswith("met_server.db")

    def test_ensure_dirs(self):
        s = Settings()
        s.ensure_dirs()
        assert s.dir_gribs.exists()

    def test_gfs_url(self):
        s = Settings()
        assert "nomads.ncep.noaa.gov" in s.gfs_url

    def test_create_date_subdirs(self):
        s = Settings()
        g, m, mt = s.create_date_subdirs("20260101", "06")
        assert g.exists() and m.exists() and mt.exists()


class TestRegion:
    def test_predefined_region_keeps_name(self):
        r = Region(name="SP")
        assert r.name == "SP"
        assert r.is_predefined is True
        assert r.kind == "estado"
        assert r.lon_min == -53.1 and r.lon_max == -44.1
        assert r.lat_min == -25.3 and r.lat_max == -19.7

    def test_city_region_bounds(self):
        r = Region(name="SP-CIDADE")
        assert r.name == "SP-CIDADE"
        assert r.kind == "cidade"
        assert r.city_name == "São Paulo"
        assert r.full_name == "Cidade de São Paulo"
        assert r.lon_min == -47.1333 and r.lon_max == -46.1333
        assert r.lat_min == -24.0505 and r.lat_max == -23.0505
        assert r.validate()

    def test_city_contains_capital(self):
        for key in ("SP-CIDADE", "RJ-CIDADE", "AM-CIDADE", "DF-CIDADE",
                    "PR-CIDADE", "RS-CIDADE", "MG-CIDADE", "PA-CIDADE",
                    "PE-CIDADE", "CE-CIDADE"):
            r = Region(name=key)
            assert r.validate(), f"{key} inválida"

    def test_state_contains_capital(self):
        capitals = {
            "SP": (-46.6333, -23.5505),
            "RJ": (-43.1964, -22.9068),
            "AM": (-60.0258, -3.1019),
            "DF": (-47.9297, -15.7801),
            "PR": (-49.2733, -25.4284),
            "RS": (-51.2253, -30.0346),
            "MG": (-43.9378, -19.9167),
            "PA": (-48.5044, -1.4558),
            "PE": (-34.8778, -8.0476),
            "CE": (-38.5428, -3.7187),
        }
        for name, (lon, lat) in capitals.items():
            r = Region(name=name)
            assert r.lon_min < lon < r.lon_max, name
            assert r.lat_min < lat < r.lat_max, name

    def test_bbox_region(self):
        r = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r.lon_min == -50
        assert r.is_predefined is False

    def test_center_region(self):
        r = Region(center_lon=-46, center_lat=-23)
        assert r.lat_min == -28 and r.lat_max == -18

    def test_validate_valid(self):
        assert Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15).validate()

    def test_validate_invalid_lon(self):
        assert not Region(lon_min=-200, lon_max=-40, lat_min=-25, lat_max=-15).validate()

    def test_get_flag(self):
        r1 = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)
        assert r1.get_flag() == 2

    def test_all_regions_exist(self):
        for name in REGIOES_PREDEFINIDAS:
            assert Region(name=name).validate()

    def test_unknown_region_raises(self):
        with pytest.raises(ValueError):
            Region(name="XX")

    def test_regioes_predefinidas_copy(self):
        assert regioes_predefinidas() == REGIOES_PREDEFINIDAS


class TestConstants:
    def test_var_map_complete(self):
        expected = [
            "ps", "prnm", "temp", "temps", "nuvem",
            "chuvaNaoConvec", "chuvaConvec", "umidadeRel",
            "u", "v", "uSupe", "vSupe",
        ]
        assert all(k in VAR_MAP for k in expected)

    def test_pressure_levels_range(self):
        assert min(PRESSURE_LEVELS) == 150
        assert max(PRESSURE_LEVELS) == 1000

    def test_unit_map(self):
        assert UNITS_MAP["temp"] == "°C"
        assert UNITS_MAP["wind"] == "m/s"


class TestProcessorHelpers:
    def test_resolve_level_within_range(self):
        p = DataProcessor()
        assert p.resolve_level("temp", 499) == 500

    def test_resolve_level_below_min(self):
        p = DataProcessor()
        assert p.resolve_level("temp", 50) == 150

    def test_resolve_level_above_max(self):
        p = DataProcessor()
        assert p.resolve_level("temp", 1200) == 1000

    def test_resolve_level_none(self):
        p = DataProcessor()
        assert p.resolve_level("temp", None) is None

    def test_resolve_level_surface_kept(self):
        p = DataProcessor()
        assert p.resolve_level("temps", 250) == 250

    def test_get_current_analysis_hour(self):
        p = DataProcessor()
        assert p.get_current_analysis_hour() in ("00", "06", "12", "18")

    def test_get_date_str_format(self):
        p = DataProcessor()
        assert len(p.get_date_str()) == 8
        assert p.get_date_str().isdigit()

    def test_convert_units_temp(self):
        p = DataProcessor()
        data, unit = p.convert_units(np.array([273.15]), "temp")
        assert np.isclose(data[0], 0.0)
        assert unit == "°C"

    def test_convert_units_pressure(self):
        p = DataProcessor()
        data, unit = p.convert_units(np.array([101325.0]), "ps")
        assert np.isclose(data[0], 1013.25)
        assert unit == "hPa"

    def test_convert_units_fallback(self):
        p = DataProcessor()
        _, unit = p.convert_units(np.array([1.0]), "u")
        assert unit == "m/s"

    def test_select_unknown_variable_raises(self):
        p = DataProcessor()
        with pytest.raises(ValueError):
            p.select_variable_from_gribs([], "inexistente")


class TestModels:
    def test_grib_request_defaults(self):
        req = GribRequest(variable=MetVariable.temp)
        assert req.level == 500
        assert req.region is None

    def test_map_request_dpi_validation(self):
        with pytest.raises(ValidationError):
            MapRequest(variable=MetVariable.temp, dpi=30)

    def test_region_name_enum(self):
        assert RegionName("SP") == RegionName.SP
