"""Cálculos de vento (ponto único de verdade) e altitude por pressão."""
from __future__ import annotations

from typing import Optional

import numpy as np

from server_MET.core.constants import NEAR_SURFACE_LEVELS

MPS_TO_KNOTS = 1.943844492
P0 = 1013.25  # hPa (atmosfera padrão)


class WindProcessor:
    def compute_speed(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.sqrt(u**2 + v**2)

    def compute_speed_knot(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.sqrt(u**2 + v**2) * MPS_TO_KNOTS

    def compute_direction_met(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        """Direção meteorológica (de onde o vento vem, 0° = N)."""
        return (180 / np.pi) * np.arctan2(-u, -v)

    def compute_direction_azimuth(self, u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return (180 / np.pi) * np.arctan2(u, v)

    def pressure_to_altitude(self, pressure_hpa: float) -> float:
        """Altura geopotencial aproximada (ft) a partir da pressão (fórmula da atmosfera padrão)."""
        if pressure_hpa <= 0:
            return 0.0
        return (1 - (pressure_hpa / P0) ** 0.190284) * 145366.45

    def get_near_surface_levels(self) -> list[int]:
        return list(NEAR_SURFACE_LEVELS)


__all__ = ["WindProcessor"]
