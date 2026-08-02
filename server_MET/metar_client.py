import json
import logging
from datetime import datetime, timezone
from typing import Optional

from server_MET.METAR import Metar
from server_MET.config import Settings

logger = logging.getLogger(__name__)

AERODROMOS: dict[str, str] = {
    "SP": "SBGR",
    "RJ": "SBGL",
    "CW": "SBCT",
    "PA": "SBPA",
    "BH": "SBCF",
    "BE": "SBBE",
    "MA": "SBEG",
    "RF": "SBRF",
    "FZ": "SBFZ",
}

NOAA_METAR_URL = "https://aviationweather.gov/api/data/metar?ids={}&format=json&hours=2"


class MetarClient:
    def __init__(self) -> None:
        self.settings = Settings()

    def fetch_metar_json(self, icao: str) -> Optional[list[dict]]:
        url = NOAA_METAR_URL.format(icao)
        try:
            from urllib.request import urlopen

            with urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info("Raw METAR JSON fetched for %s", icao)
                return data
        except Exception as e:
            logger.error("Failed to fetch raw METAR for %s: %s", icao, e)
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
            parsed = {
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
            }
            return parsed
        except Exception as e:
            logger.error("Failed to parse METAR for %s: %s", icao, e)
            return None

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
        )
        return {k: entry.get(k) for k in keys if k in entry}

    def get_metar(self, icao: str) -> Optional[dict]:
        data = self.fetch_metar_json(icao)
        if data is None:
            return None
        raw_text = self.extract_raw_text_from_json(data)
        if raw_text is None:
            return None
        parsed = self.get_parsed_metar(icao, raw_text)
        result = {
            "station": icao,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_metar": raw_text,
        }
        metadata = self._extract_metadata(data)
        if metadata:
            result["metadata"] = metadata
        if parsed:
            result["parsed"] = parsed
        return result

    def get_metar_light(self, icao: str) -> Optional[str]:
        raw_text = self.get_raw_metar(icao)
        if raw_text is None:
            logger.error("Failed to fetch raw METAR light for %s", icao)
            return None
        return raw_text

    def get_metar_for_region(self, region: str) -> Optional[dict]:
        region = region.upper()
        if region not in AERODROMOS:
            logger.warning("Unknown region: %s", region)
            return None
        icao = AERODROMOS[region]
        return self.get_metar(icao)

    def get_all_metars(self) -> list[dict]:
        results = []
        for region, icao in AERODROMOS.items():
            try:
                result = self.get_metar(icao)
                if result:
                    result["region"] = region
                    results.append(result)
            except Exception as e:
                logger.error("Error fetching METAR for %s: %s", region, e)
        return results

    def metar_to_json(self, icao: str) -> Optional[str]:
        data = self.get_metar(icao)
        if data is None:
            return None
        return json.dumps(data, indent=2, ensure_ascii=False)
