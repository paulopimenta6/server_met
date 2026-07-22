import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from server_MET.METAR import Metar, NOAAServError
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

NOAA_METAR_URL = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString={}&hoursBeforeNow=2"


class MetarClient:
    def __init__(self) -> None:
        self.settings = Settings()

    def fetch_raw_xml(self, icao: str) -> Optional[str]:
        url = NOAA_METAR_URL.format(icao)
        try:
            from urllib.request import urlopen
            with urlopen(url, timeout=30) as response:
                data = response.read().decode("utf-8")
                logger.info("Raw METAR XML fetched for %s", icao)
                return data
        except Exception as e:
            logger.error("Failed to fetch raw METAR for %s: %s", icao, e)
            return None

    def extract_raw_text_from_xml(self, xml_data: str) -> Optional[str]:
        try:
            root = ET.fromstring(xml_data)
            for metar in root.iter("raw_text"):
                return metar.text
            for data_set in root.iter("data"):
                for metar in data_set.iter("raw_text"):
                    return metar.text
            return None
        except ET.ParseError as e:
            logger.error("XML parse error: %s", e)
            return None

    def get_raw_metar(self, icao: str) -> Optional[str]:
        xml = self.fetch_raw_xml(icao)
        if xml is None:
            return None
        return self.extract_raw_text_from_xml(xml)

    def get_parsed_metar(self, icao: str, raw_text: str) -> Optional[dict]:
        try:
            metar_obj = Metar(icao, text=raw_text)
            props = metar_obj.getAll()
            parsed = {
                "station": props.get("metar", {}),
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

    def get_metar(self, icao: str) -> Optional[dict]:
        raw_text = self.get_raw_metar(icao)
        if raw_text is None:
            return None
        parsed = self.get_parsed_metar(icao, raw_text)
        result = {
            "station": icao,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_metar": raw_text,
        }
        if parsed:
            result["parsed"] = parsed
        return result

    def get_metar_light(self, icao: str) -> Optional[str]:
        try:
            metar_obj = Metar(icao)
            return metar_obj.metar
        except NOAAServError as e:
            logger.error("NOAA server error for %s: %s", icao, e)
            return None
        except Exception as e:
            logger.error("Failed to fetch METAR light for %s: %s", icao, e)
            return None

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
