from typing import Optional


REGIOES_PREDEFINIDAS: dict[str, tuple[float, float, float, float]] = {
    "SP": (-56, -42, -28, -18),
    "RJ": (-46, -36, -27, -17),
    "AM": (-65, -55, -7, 7),
    "DF": (-54, -44, -20, -10),
    "PR": (-54, -44, -30, -20),
    "RS": (-56, -46, -34, -24),
    "MG": (-48, -38, -24, -14),
    "PA": (-53, -43, -6, 4),
    "PE": (-39, -29, -13, -3),
    "CE": (-43, -33, -8, 2),
    "SA": (-100, -20, -60, 25),
}


class Region:
    def __init__(
        self,
        name: Optional[str] = None,
        lon_min: Optional[float] = None,
        lon_max: Optional[float] = None,
        lat_min: Optional[float] = None,
        lat_max: Optional[float] = None,
        center_lon: Optional[float] = None,
        center_lat: Optional[float] = None,
    ) -> None:
        if name:
            self._load_predefined(name)
        elif all(v is not None for v in [lon_min, lon_max, lat_min, lat_max]):
            self.lon_min = float(lon_min)
            self.lon_max = float(lon_max)
            self.lat_min = float(lat_min)
            self.lat_max = float(lat_max)
        elif all(v is not None for v in [center_lon, center_lat]):
            self._from_center(center_lon, center_lat)
        else:
            raise ValueError(
                "Provide a region name, bounding box, or center coordinates"
            )

    def _load_predefined(self, name: str) -> None:
        name = name.upper()
        if name not in REGIOES_PREDEFINIDAS:
            raise ValueError(f"Unknown region: {name}. Options: {list(REGIOES_PREDEFINIDAS.keys())}")
        lon_min, lon_max, lat_min, lat_max = REGIOES_PREDEFINIDAS[name]
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_min = lat_min
        self.lat_max = lat_max

    def _from_center(self, lon: float, lat: float) -> None:
        self.lat_min = max(-85, lat - 5)
        self.lat_max = min(85, lat + 5)
        self.lon_min = lon - 5
        self.lon_max = lon + 5
        if self.lon_min < -180:
            self.lon_min = -180
        if self.lon_max > 180:
            self.lon_max = 180

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.lon_min, self.lon_max, self.lat_min, self.lat_max)

    @property
    def name(self) -> str:
        return (
            f"LonMin:{self.lon_min}_LonMax:{self.lon_max}"
            f"_LatMin:{self.lat_min}_LatMax:{self.lat_max}"
        )

    def validate(self) -> bool:
        if not (-180 <= self.lon_min <= 180 and -180 <= self.lon_max <= 180):
            return False
        if not (-90 <= self.lat_min <= 90 and -90 <= self.lat_max <= 90):
            return False
        if self.lon_min >= self.lon_max:
            return False
        if self.lat_min >= self.lat_max:
            return False
        return True

    def get_flag(self) -> int:
        if 0 <= self.lon_min < 180 and 0 <= self.lon_max < 180:
            return 1
        if -180 <= self.lon_min < 0 and -180 <= self.lon_max < 0:
            return 2
        if -180 <= self.lon_min < 0 and 0 <= self.lon_max < 180:
            return 3
        return 0


def regioes_predefinidas() -> dict:
    return REGIOES_PREDEFINIDAS.copy()
