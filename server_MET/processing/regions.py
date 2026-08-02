"""Regiões predefinidas e seleção de região (nome, bbox ou centro).

Desde a v4, cada localidade tem dois níveis de enquadramento:
- **Estado** (chave como ``SP``): caixa que cobre o estado inteiro.
- **Cidade** (chave como ``SP-CIDADE``): caixa pequena (±0.5°) em torno da
  capital, de modo que a cidade inteira fique visível no mapa.
"""
from __future__ import annotations

from typing import Optional

#: (lon_min, lon_max, lat_min, lat_max) — bboxes precisas dos ESTADOS.
REGIOES_PREDEFINIDAS: dict[str, tuple[float, float, float, float]] = {
    "SP": (-53.10, -44.10, -25.30, -19.70),
    "RJ": (-45.00, -40.80, -23.40, -20.70),
    "AM": (-73.80, -56.00, -9.20, 4.50),
    "DF": (-48.30, -47.30, -16.10, -15.50),
    "PR": (-54.60, -48.00, -26.70, -22.50),
    "RS": (-57.60, -49.60, -33.70, -27.00),
    "MG": (-51.00, -39.80, -22.90, -14.20),
    "PA": (-58.90, -46.00, -9.80, 2.40),
    "PE": (-41.40, -34.80, -9.50, -7.10),
    "CE": (-41.40, -37.20, -7.90, -2.40),
    "SA": (-100.00, -20.00, -60.00, 25.00),
}

#: Países da América do Sul: chave -> bbox (lon_min, lon_max, lat_min, lat_max).
PAISES_AMERICA_DO_SUL: dict[str, tuple[float, float, float, float]] = {
    "AR": (-73.50, -53.60, -55.10, -21.80),
    "BO": (-69.60, -57.50, -22.90, -9.70),
    "BR": (-74.00, -34.80, -33.80, 5.30),
    "CL": (-75.60, -66.90, -56.00, -17.50),
    "CO": (-79.10, -66.90, -4.20, 12.50),
    "EC": (-81.00, -75.20, -5.00, 1.40),
    "GY": (-61.40, -56.50, 1.10, 8.60),
    "PY": (-62.60, -54.20, -27.60, -19.30),
    "PEU": (-81.30, -68.70, -18.40, -0.03),
    "SR": (-58.10, -53.90, 1.80, 6.00),
    "UY": (-58.40, -53.10, -34.90, -30.10),
    "VE": (-73.40, -59.80, 0.60, 12.20),
}

#: Raio (graus) da caixa em torno do centro da capital para o mapa da cidade.
CIDADE_RAIO_GRAUS: float = 0.5

#: Cidades predefinidas: chave -> (nome da cidade, lon, lat).
#: A caixa do mapa é calculada como centro ± CIDADE_RAIO_GRAUS.
CIDADES_PREDEFINIDAS: dict[str, tuple[str, float, float]] = {
    "SP-CIDADE": ("São Paulo", -46.6333, -23.5505),
    "RJ-CIDADE": ("Rio de Janeiro", -43.1964, -22.9068),
    "AM-CIDADE": ("Manaus", -60.0258, -3.1019),
    "DF-CIDADE": ("Brasília", -47.9297, -15.7801),
    "PR-CIDADE": ("Curitiba", -49.2733, -25.4284),
    "RS-CIDADE": ("Porto Alegre", -51.2253, -30.0346),
    "MG-CIDADE": ("Belo Horizonte", -43.9378, -19.9167),
    "PA-CIDADE": ("Belém", -48.5044, -1.4558),
    "PE-CIDADE": ("Recife", -34.8778, -8.0476),
    "CE-CIDADE": ("Fortaleza", -38.5428, -3.7187),
}

#: Descrições amigáveis por região (exibição e documentação).
REGIOES_DESCRICOES: dict[str, str] = {
    "SP": "Estado de São Paulo",
    "RJ": "Estado do Rio de Janeiro",
    "AM": "Estado do Amazonas",
    "DF": "Distrito Federal",
    "PR": "Estado do Paraná",
    "RS": "Estado do Rio Grande do Sul",
    "MG": "Estado de Minas Gerais",
    "PA": "Estado do Pará",
    "PE": "Estado de Pernambuco",
    "CE": "Estado do Ceará",
    "SA": "América do Sul (visão geral)",
    "AR": "Argentina",
    "BO": "Bolívia",
    "BR": "Brasil",
    "CL": "Chile",
    "CO": "Colômbia",
    "EC": "Equador",
    "GY": "Guiana",
    "PY": "Paraguai",
    "PEU": "Peru",
    "SR": "Suriname",
    "UY": "Uruguai",
    "VE": "Venezuela",
    "SP-CIDADE": "Cidade de São Paulo",
    "RJ-CIDADE": "Cidade do Rio de Janeiro",
    "AM-CIDADE": "Cidade de Manaus",
    "DF-CIDADE": "Cidade de Brasília",
    "PR-CIDADE": "Cidade de Curitiba",
    "RS-CIDADE": "Cidade de Porto Alegre",
    "MG-CIDADE": "Cidade de Belo Horizonte",
    "PA-CIDADE": "Cidade de Belém",
    "PE-CIDADE": "Cidade de Recife",
    "CE-CIDADE": "Cidade de Fortaleza",
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
    "AR": "SAEZ",
    "BO": "SLLP",
    "BR": "SBGR",
    "CL": "SCEL",
    "CO": "SKBO",
    "EC": "SEQM",
    "GY": "SYCJ",
    "PY": "SGAS",
    "PEU": "SPIM",
    "SR": "SMJP",
    "UY": "SUMU",
    "VE": "SVMI",
}


def _cidade_bbox(lon: float, lat: float, raio: float = CIDADE_RAIO_GRAUS):
    return (
        max(-180, lon - raio),
        min(180, lon + raio),
        max(-90, lat - raio),
        min(90, lat + raio),
    )


class Region:
    """Região geográfica com nome preservado (quando predefinida).

    Aceita: nome predefinido (estado como ``SP`` ou cidade como ``SP-CIDADE``),
    bbox (lon_min/lon_max/lat_min/lat_max) ou centro (lon/lat com raio padrão
    de ±5°).
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
        self._kind: str = "bbox"
        self._city_name: Optional[str] = None
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
        if name in CIDADES_PREDEFINIDAS:
            city_name, lon, lat = CIDADES_PREDEFINIDAS[name]
            self._name = name
            self._kind = "cidade"
            self._city_name = city_name
            self.lon_min, self.lon_max, self.lat_min, self.lat_max = _cidade_bbox(
                lon, lat
            )
            return
        if name in PAISES_AMERICA_DO_SUL:
            self._name = name
            self._kind = "pais"
            lon_min, lon_max, lat_min, lat_max = PAISES_AMERICA_DO_SUL[name]
            self.lon_min = lon_min
            self.lon_max = lon_max
            self.lat_min = lat_min
            self.lat_max = lat_max
            return
        if name not in REGIOES_PREDEFINIDAS:
            raise ValueError(
                f"Região desconhecida: {name}. Opções: "
                f"{list(REGIOES_PREDEFINIDAS) + list(PAISES_AMERICA_DO_SUL) + list(CIDADES_PREDEFINIDAS)}"
            )
        self._name = name
        self._kind = "estado" if name != "SA" else "visao_geral"
        lon_min, lon_max, lat_min, lat_max = REGIOES_PREDEFINIDAS[name]
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_min = lat_min
        self.lat_max = lat_max

    def _from_center(self, lon: float, lat: float) -> None:
        self._kind = "centro"
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
    def kind(self) -> str:
        """Tipo da região: estado, cidade, visao_geral, bbox ou centro."""
        return self._kind

    @property
    def city_name(self) -> Optional[str]:
        return self._city_name

    @property
    def full_name(self) -> str:
        """Nome completo exibido em títulos e arquivos (ex.: 'Cidade de São Paulo')."""
        if self._name:
            return REGIOES_DESCRICOES.get(self._name, self._name)
        return self.name

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


def cidades_predefinidas() -> dict:
    """Retorna o centro (lon, lat) de cada cidade predefinida."""
    return {k: (v[1], v[2]) for k, v in CIDADES_PREDEFINIDAS.items()}


def todas_as_regioes() -> dict[str, tuple[float, float, float, float]]:
    """Estados + países da América do Sul + cidades com as respectivas bboxes."""
    result = dict(REGIOES_PREDEFINIDAS)
    result.update(PAISES_AMERICA_DO_SUL)
    for key, (city_name, lon, lat) in CIDADES_PREDEFINIDAS.items():
        result[key] = _cidade_bbox(lon, lat)
    return result


__all__ = [
    "Region",
    "REGIOES_PREDEFINIDAS",
    "PAISES_AMERICA_DO_SUL",
    "CIDADES_PREDEFINIDAS",
    "CIDADE_RAIO_GRAUS",
    "REGIOES_DESCRICOES",
    "REGIOES_ICAO",
    "regioes_predefinidas",
    "cidades_predefinidas",
    "todas_as_regioes",
]
