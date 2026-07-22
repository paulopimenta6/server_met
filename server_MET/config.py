import os
from pathlib import Path
from typing import Optional


class Settings:
    _instance: Optional["Settings"] = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent
        self.ENV_FILE = self.PROJECT_ROOT / "environment" / "path.conf"
        self._dir_gribs: Optional[str] = None
        self._dir_mapas: Optional[str] = None
        self._dir_matrizes: Optional[str] = None
        self._dir_matrizes_predi: Optional[str] = None
        self._dir_matrizes_bluesky: Optional[str] = None
        self._parse_env_file()

    def _parse_env_file(self) -> None:
        if self.ENV_FILE.exists():
            with open(self.ENV_FILE) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if key == "dir_gribs":
                            self._dir_gribs = value
                        elif key == "dir_mapas":
                            self._dir_mapas = value
                        elif key == "dir_matrizes":
                            self._dir_matrizes = value
                        elif key == "dir_matrizes_predi":
                            self._dir_matrizes_predi = value
                        elif key == "dir_matrizes_bluesky":
                            self._dir_matrizes_bluesky = value

    def _resolve_dir(self, path_str: Optional[str], default_subdir: str) -> Path:
        if path_str:
            p = Path(path_str)
            if p.is_absolute():
                return p
            return self.PROJECT_ROOT / p
        return self.PROJECT_ROOT / default_subdir

    @property
    def dir_gribs(self) -> Path:
        return self._resolve_dir(self._dir_gribs, "data/gribs")

    @property
    def dir_mapas(self) -> Path:
        return self._resolve_dir(self._dir_mapas, "data/mapasGrib")

    @property
    def dir_matrizes(self) -> Path:
        return self._resolve_dir(self._dir_matrizes, "data/matrizGrib")

    @property
    def dir_matrizes_predi(self) -> Path:
        return self._resolve_dir(self._dir_matrizes_predi, "data/matrizGrib/predi")

    @property
    def dir_matrizes_bluesky(self) -> Path:
        return self._resolve_dir(self._dir_matrizes_bluesky, "data/matrizGrib/bluesky")

    @property
    def gfs_url(self) -> str:
        return "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs."

    def ensure_dirs(self) -> None:
        for d in [
            self.dir_gribs,
            self.dir_mapas,
            self.dir_matrizes,
            self.dir_matrizes_predi,
            self.dir_matrizes_bluesky,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def create_date_subdirs(self, date_str: str, hour: str) -> tuple[Path, Path, Path]:
        grib_dir = self.dir_gribs / date_str / hour
        grib_dir.mkdir(parents=True, exist_ok=True)

        map_dir = self.dir_mapas / date_str / hour
        map_dir.mkdir(parents=True, exist_ok=True)

        mat_dir = self.dir_matrizes / date_str / hour
        mat_dir.mkdir(parents=True, exist_ok=True)

        return grib_dir, map_dir, mat_dir
