import logging
from typing import Optional

import numpy as np

from server_MET.data_processor import DataProcessor

logger = logging.getLogger(__name__)

VAR_NIVEL_PROX_SUPE = [20, 30, 40, 50, 80]


class WindProcessor:
    def __init__(self) -> None:
        self.processor = DataProcessor()

    def compute_speed(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.sqrt(u**2 + v**2)

    def compute_speed_knot(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.sqrt(u**2 + v**2) * 1.943

    def compute_direction_met(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return (180 / np.pi) * np.arctan2(-u, -v)

    def compute_direction_azimuth(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return (180 / np.pi) * np.arctan2(u, v)

    def pressure_to_altitude(self, pressure_hpa: float) -> float:
        p0 = 1013.25
        h_alt = (1 - (pressure_hpa / p0) ** 0.190284) * 145366.45
        return h_alt

    def get_near_surface_levels(self) -> list[int]:
        return VAR_NIVEL_PROX_SUPE

    def process_upper_wind(
        self,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
        level: int = 500,
    ) -> tuple[list, list]:
        resolved_level = self.processor.resolve_level("u", level)
        grib_objs = self.processor.load_gribs(date_str, analysis)
        u_msgs = self.processor.select_variable_from_gribs(
            grib_objs, "u", resolved_level
        )
        v_msgs = self.processor.select_variable_from_gribs(
            grib_objs, "v", resolved_level
        )
        return u_msgs, v_msgs

    def process_surface_wind(
        self,
        date_str: Optional[str] = None,
        analysis: Optional[str] = None,
    ) -> dict[int, tuple[list, list]]:
        grib_objs = self.processor.load_gribs(date_str, analysis)
        results = {}
        for level in VAR_NIVEL_PROX_SUPE:
            u_msgs = self.processor.select_variable_from_gribs(
                grib_objs, "uSupe", level
            )
            v_msgs = self.processor.select_variable_from_gribs(
                grib_objs, "vSupe", level
            )
            results[level] = (u_msgs, v_msgs)
        return results
