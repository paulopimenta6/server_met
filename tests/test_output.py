"""Testes dos geradores de saída (offline, sem GRIB): mapas, matrizes e BlueSky."""
from server_MET.output.maps import HAS_MAP_BACKEND, MapGenerator
from server_MET.output.matrices import MatrixGenerator
from server_MET.processing.regions import Region


class TestMapGenerator:
    def test_map_backend_available(self):
        assert HAS_MAP_BACKEND is True

    def test_generate_without_grib_returns_empty(self, isolated_db, tmp_path):
        gen = MapGenerator()
        files = gen.generate(
            "temp", Region(name="SP"), 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert files == []

    def test_generate_wind_without_grib_returns_empty(self, isolated_db, tmp_path):
        gen = MapGenerator()
        files = gen.generate(
            "wind", Region(name="SP"), 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert files == []


class TestMatrixGenerator:
    def test_generate_without_grib_returns_empty(self, isolated_db, tmp_path):
        gen = MatrixGenerator()
        files = gen.generate(
            "temp", Region(name="SP"), 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert files == []

    def test_generate_wind_without_grib_returns_empty(self, isolated_db, tmp_path):
        gen = MatrixGenerator()
        files = gen.generate(
            "wind", Region(name="SP"), 500,
            "20990101", "06", output_dir=str(tmp_path),
        )
        assert files == []

    def test_bluesky_without_grib_returns_none(self, isolated_db):
        gen = MatrixGenerator()
        assert gen.generate_bluesky(Region(name="SP"), 500, "20990101", "06") is None
