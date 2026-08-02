"""Consolidação por região: estado de dados e análises de uma região predefinida."""
from __future__ import annotations

from typing import Optional

from server_MET.acquisition.grib_reader import GribReader
from server_MET.acquisition.metar_client import AERODROMOS, MetarClient
from server_MET.core.config import Settings
from server_MET.core.logging_conf import get_logger
from server_MET.processing.regions import REGIOES_ICAO, REGIOES_PREDEFINIDAS

logger = get_logger(__name__)


class RegionSummary:
    """Visão consolidada de uma região: dados disponíveis, variáveis e METAR."""

    def __init__(self, reader: Optional[GribReader] = None, metar: Optional[MetarClient] = None) -> None:
        self.settings = Settings()
        self.reader = reader or GribReader()
        self.metar = metar or MetarClient()

    def summary(self, region_name: str) -> dict:
        region_name = region_name.upper()
        if region_name not in REGIOES_PREDEFINIDAS:
            return {"region": region_name, "error": f"Região desconhecida: {region_name}"}

        bounds = REGIOES_PREDEFINIDAS[region_name]
        grib_dir = self.settings.dir_gribs
        dates = sorted(d.name for d in grib_dir.iterdir() if d.is_dir() and d.name.isdigit())
        dates = dates[-5:]

        available = []
        for date in dates:
            for ana in self.reader.find_available_analyses(date):
                res = self.reader.find_available_resolutions(date, ana)
                if res:
                    available.append({"date": date, "analysis": ana, "resolutions": res})

        metar_info = None
        icao = REGIOES_ICAO.get(region_name)
        if icao:
            metar_info = {
                "icao": icao,
                "station": AERODROMOS.get(region_name, icao),
                "available": True,
            }

        return {
            "region": region_name,
            "bounds": list(bounds),
            "description": "região predefinida",
            "icao_reference": icao,
            "data_available": available,
            "metar": metar_info,
        }


__all__ = ["RegionSummary"]
