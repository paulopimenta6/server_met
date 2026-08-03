"""Cliente METAR — fetch na API JSON da aviationweather.gov + parser vendado.

Cada observação recuperada é persistida na tabela `metar_obs` (arquivo histórico).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from server_MET.METAR import Metar
from server_MET.core.constants import NOAA_METAR_URL
from server_MET.persistence.repositories import MetarRepository
from server_MET.processing.regions import REGIOES_ICAO

logger = logging.getLogger(__name__)

#: Região (estado/cidade/país) -> aeródromo de referência (ICAO).
#: Derivado de `REGIOES_ICAO` (regions.py) para manter fonte única.
AERODROMOS: dict[str, str] = {
    k: v for k, v in REGIOES_ICAO.items() if v
}


class MetarClient:
    def __init__(self, repositories: Optional[MetarRepository] = None) -> None:
        self.repo = repositories or MetarRepository()

    def fetch_metar_json(self, icao: str) -> Optional[list[dict]]:
        url = NOAA_METAR_URL.format(icao)
        try:
            from urllib.request import urlopen

            with urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info("METAR JSON obtido para %s", icao)
                return data
        except Exception as e:
            logger.error("Falha ao obter METAR de %s: %s", icao, e)
            return None

    def extract_raw_text_from_json(self, data: Optional[list[dict]]) -> Optional[str]:
        if not data:
            return None
        for entry in data:
            raw = entry.get("rawOb")
            if raw:
                return raw
        return None

    def get_raw_metar(self, icao: str) -> Optional[str]:
        data = self.fetch_metar_json(icao)
        if data is None:
            return None
        return self.extract_raw_text_from_json(data)

    def get_parsed_metar(self, icao: str, raw_text: str) -> Optional[dict]:
        try:
            metar_obj = Metar(icao, text=raw_text)
            props = metar_obj.getAll()
            result = {
                "station": icao,
                "station_code": icao,
                "observation": props.get("dateTime"),
                "auto": props.get("auto"),
                "wind": props.get("wind"),
                "visibility": props.get("visibility"),
                "rvr": props.get("rvr"),
                "weather": props.get("weather"),
                "cloud": props.get("cloud"),
                "temperatures": props.get("temperatures"),
                "qnh": props.get("qnh"),
                "changements": props.get("changements"),
                "vmc": props.get("vmc"),
                "runway": props.get("runway"),
                "recent": props.get("recent"),
                "trend": props.get("trend"),
                "qfe": props.get("qfe"),
                "sea_level_pressure": props.get("sea_level_pressure"),
                "pressure_tendency": props.get("pressure_tendency"),
                "max_temp": props.get("max_temp"),
                "min_temp": props.get("min_temp"),
                "precipitation": props.get("precipitation"),
                "sunshine": props.get("sunshine"),
                "snow_depth": props.get("snow_depth"),
                "present_weather": props.get("present_weather"),
                "cloud_type": props.get("cloud_type"),
                "cloud_base": props.get("cloud_base"),
                "cloud_amount": props.get("cloud_amount"),
                "wind_shear": props.get("wind_shear"),
                "icing": props.get("icing"),
                "turbulence": props.get("turbulence"),
                "remarks": props.get("remarks"),
                "metar_type": props.get("metar_type"),
                "corrected": props.get("corrected"),
            }
            self._enrich_derived_fields(result)
            return result
        except Exception as e:
            logger.error("Falha ao decodificar METAR de %s: %s", icao, e)
            return None

    @staticmethod
    def _enrich_derived_fields(parsed: dict) -> None:
        """Adiciona campos derivados (conversões) ao dict já decodificado."""
        wind = parsed.get("wind")
        if isinstance(wind, dict) and wind.get("speed") is not None:
            speed_kt = wind["speed"]
            wind["speed_kmh"] = round(speed_kt * 1.852, 1)
            if wind.get("gust") is not None:
                wind["gust_kmh"] = round(wind["gust"] * 1.852, 1)
            if wind.get("dir") is not None:
                wind["dir_cardinal"] = MetarClient._deg_to_cardinal(wind["dir"])

        temps = parsed.get("temperatures")
        if isinstance(temps, dict):
            try:
                t = float(temps.get("temp", 0))
                d = float(temps.get("dewpoint", 0))
                temps["humidity"] = round(
                    100 * (1 - (t - d) / (273.15 + t)), 1
                ) if (273.15 + t) else None
            except (TypeError, ValueError):
                pass

        visibility = parsed.get("visibility")
        if isinstance(visibility, int):
            parsed["visibility_km"] = round(visibility / 1000, 1) if visibility else None

        qnh = parsed.get("qnh")
        if isinstance(qnh, (int, float)):
            parsed["qnh_hpa"] = qnh
            parsed["qnh_inhg"] = round(qnh * 0.02953, 2)

    @staticmethod
    def _deg_to_cardinal(deg: float) -> str:
        """Converte graus para direção cardinal."""
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((deg + 11.25) / 22.5) % 16
        return dirs[idx]

    def _extract_metadata(self, data: Optional[list[dict]]) -> Optional[dict]:
        if not data:
            return None
        entry = data[0]
        keys = (
            "icaoId",
            "obsTime",
            "reportTime",
            "temp",
            "dewp",
            "wdir",
            "wspd",
            "visib",
            "altim",
            "metarType",
            "lat",
            "lon",
            "elev",
            "name",
        )
        return {k: entry.get(k) for k in keys if k in entry}

    def get_metar(self, icao: str, region: Optional[str] = None) -> Optional[dict]:
        data = self.fetch_metar_json(icao)
        if data is None:
            return None
        raw_text = self.extract_raw_text_from_json(data)
        if raw_text is None:
            return None
        parsed = self.get_parsed_metar(icao, raw_text)
        metadata = self._extract_metadata(data)
        result = {
            "station": icao,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_metar": raw_text,
        }
        if metadata:
            result["metadata"] = metadata
        if parsed:
            result["parsed"] = parsed

        obs_time = metadata.get("obsTime") if metadata else None
        if obs_time is not None:
            obs_time = str(obs_time)
        self.repo.upsert(
            icao=icao,
            raw_metar=raw_text,
            parsed=parsed,
            metadata=metadata,
            region=region,
            obs_time=obs_time,
        )
        return result

    def get_metar_light(self, icao: str) -> Optional[str]:
        raw_text = self.get_raw_metar(icao)
        if raw_text is None:
            logger.error("Falha ao obter METAR light de %s", icao)
            return None
        return raw_text

    def get_metar_for_region(self, region: str) -> Optional[dict]:
        region = region.upper()
        if region not in AERODROMOS:
            logger.warning("Região desconhecida: %s", region)
            return None
        icao = AERODROMOS[region]
        return self.get_metar(icao, region=region)

    def get_all_metars(self) -> list[dict]:
        results = []
        for region, icao in AERODROMOS.items():
            try:
                result = self.get_metar(icao, region=region)
                if result:
                    result["region"] = region
                    results.append(result)
            except Exception as e:
                logger.error("Erro ao obter METAR de %s: %s", region, e)
        return results

    def metar_to_json(self, icao: str) -> Optional[str]:
        data = self.get_metar(icao)
        if data is None:
            return None
        return json.dumps(data, indent=2, ensure_ascii=False)


__all__ = ["MetarClient", "AERODROMOS"]
