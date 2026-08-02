"""Regiões predefinidas e seleção de região (nome, bbox ou centro)."""
from __future__ import annotations

from typing import Optional

#: (lon_min, lon_max, lat_min, lat_max)
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

#: Descrições amigáveis por região (exibição e documentação).
REGIOES_DESCRICOES: dict[str, str] = {
    "SP": "São Paulo e entorno",
    "RJ": "Rio de Janeiro e entorno",
    "AM": "Amazonas (região de Manaus)",
    "DF": "Distrito Federal / Centro-Oeste",
    "PR": "Paraná",
    "RS": "Rio Grande do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará (região de Belém)",
    "PE": "Pernambuco (região de Recife)",
    "CE": "Ceará (região de Fortaleza)",
    "SA": "América do Sul (visão geral)",
}

#: Aeródromo de referência por região (para METAR).
REGIOES_ICAO: dict[str, str] = {
    "SP": "SBGR",
    "RJ": "SBGL",
    "AM": "SBEG",
    "DF": "SBBR",
    "PR": "SBCT",
    "RS": "SBPA",
    "MG": "SBCF",
    "PA": "SBBE",
    "PE": "SBRF",
    "CE": "SBFZ",
    "SA": None,
}


class Region:
    """Região geográfica com nome preservado (quando predefinida).

    Aceita: nome predefinido, bbox (lon_min/lon_max/lat_min/lat_max) ou
    centro (lon/lat com raio padrão de ±5°).
    """

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
        self._name: Optional[str] = None
        if name:
            self._load_predefined(name)
        elif all(v is not None for v in [lon_min, lon_max, lat_min, lat_max]):
            self.lon_min = float(lon_min)
            self.lon_max = float(lon_max)
            self.lat_min = float(lat_min)
            self.lat_max = float(lat_max)
        elif all(v is not None for v in [center_lon, center_lat]):
            self._from_center(float(center_lon), float(center_lat))
        else:
            raise ValueError(
                "Informe um nome de região, bounding box ou coordenadas centrais"
            )

    def _load_predefined(self, name: str) -> None:
        name = name.upper()
        if name not in REGIOES_PREDEFINIDAS:
            raise ValueError(
                f"Região desconhecida: {name}. Opções: {list(REGIOES_PREDEFINIDAS)}"
            )
        self._name = name
        lon_min, lon_max, lat_min, lat_max = REGIOES_PREDEFINIDAS[name]
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_min = lat_min
        self.lat_max = lat_max

    def _from_center(self, lon: float, lat: float) -> None:
        self.lat_min = max(-85, lat - 5)
        self.lat_max = min(85, lat + 5)
        self.lon_min = max(-180, lon - 5)
        self.lon_max = min(180, lon + 5)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.lon_min, self.lon_max, self.lat_min, self.lat_max)

    @property
    def name(self) -> str:
        """Nome amigável; para regiões por bbox/centro gera nome descritivo."""
        if self._name:
            return self._name
        return (
            f"LonMin:{self.lon_min}_LonMax:{self.lon_max}"
            f"_LatMin:{self.lat_min}_LatMax:{self.lat_max}"
        )

    @property
    def is_predefined(self) -> bool:
        return self._name is not None

    def validate(self) -> bool:
        if not (-180 <= self.lon_min <= 180 and -180 <= self.lon_max <= 180):
            return False
        if not (-90 <= self.lat_min <= 90 and -90 <= self.lat_max <= 90):
            return False
        if self.lon_min >= self.lon_max or self.lat_min >= self.lat_max:
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


__all__ = ["Region", "REGIOES_PREDEFINIDAS", "REGIOES_DESCRICOES", "REGIOES_ICAO", "regioes_predefinidas"]
