#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regiões predefinidas do Server MET v2.0 - 18 regiões total
"""
from typing import Dict, Tuple, List, Optional
from core.config import REGIOES

class RegioesPredefinidas:
    def __init__(self):
        self.regioes = REGIOES
    
    def get_region(self, codigo: str) -> Optional[Dict[str, float]]:
        return self.regioes.get(codigo.upper())
    
    def get_all_regions(self) -> Dict[str, Dict[str, float]]:
        return self.regioes.copy()
    
    def get_region_bounds(self, codigo: str) -> Optional[Tuple[float, float, float, float]]:
        regiao = self.get_region(codigo)
        if regiao:
            return (regiao["lon_min"], regiao["lon_max"], regiao["lat_min"], regiao["lat_max"])
        return None
    
    def get_lons_lats(self, codigo: str) -> Optional[List[Tuple[float, float]]]:
        bounds = self.get_region_bounds(codigo)
        if bounds:
            lon_min, lon_max, lat_min, lat_max = bounds
            return [(lon_min, lon_max), (lat_min, lat_max)]
        return None
    
    def list_codes(self) -> List[str]:
        return list(self.regioes.keys())
    
    def validate_region(self, codigo: str) -> bool:
        return codigo.upper() in self.regioes

class PontoRegiao:
    def __init__(self, lon: float, lat: float, buffer_graus: float = 2.0):
        self.lon = lon
        self.lat = lat
        self.buffer = buffer_graus
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        return (
            self.lon - self.buffer,
            self.lon + self.buffer,
            self.lat - self.buffer,
            self.lat + self.buffer
        )
    
    def get_lons_lats(self) -> List[Tuple[float, float]]:
        lon_min, lon_max, lat_min, lat_max = self.get_bounds()
        return [(lon_min, lon_max), (lat_min, lat_max)]

def get_regioes_instance() -> RegioesPredefinidas:
    return RegioesPredefinidas()