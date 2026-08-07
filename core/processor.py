#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de dados meteorológicos e de poluição - Server MET v2.0
Refatorado de processamento_dados_MET.py
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from core.variables import get_variable_info, convert_value, get_pollution_variables, level_is_meaningful
from core.grib_reader import GribReader
from core.config import NIVEIS_ISOBARICOS

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, grib_reader: GribReader):
        self.reader = grib_reader
    
    def extract_variable(
        self,
        file_path: str,
        var_code: str,
        level: Optional[int] = None,
        region_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[Dict[str, Any]]:
        var_info = get_variable_info(var_code)
        if not var_info:
            logger.error(f"Unknown variable code: {var_code}")
            return None
        
        # For level types without a meaningful numeric level (atmosphere,
        # hybrid, tropopause, depthBelowLandLayer, ...) match on name + type only.
        sel_level = level if level_is_meaningful(var_info["level_type"]) else None
        messages = self.reader.select_messages(
            file_path,
            name=var_info["grib_name"],
            level_type=var_info["level_type"],
            level=sel_level
        )

        if not messages:
            logger.warning(f"No messages found for {var_code} at level {level} in {file_path}")
            return None

        msg = messages[0]
        
        if region_bounds:
            lon_min, lon_max, lat_min, lat_max = region_bounds
            # Convert longitudes from -180/180 to 0/360 if needed (GRIB uses 0-360)
            if lon_min < 0:
                lon_min += 360
            if lon_max < 0:
                lon_max += 360
            try:
                data, lats, lons = msg.data(lat1=lat_min, lat2=lat_max, lon1=lon_min, lon2=lon_max)
            except Exception as e:
                logger.error(f"Error extracting region data: {e}")
                return None
        else:
            data = msg.values
            lats, lons = msg.latlons()
        
        converted_data = convert_value(var_code, data)
        
        return {
            "variable_code": var_code,
            "variable_name": var_info["grib_name"],
            "level_type": var_info["level_type"],
            "level": level if level is not None else msg.level,
            "unit": var_info["unit"],
            "data": converted_data,
            "lats": lats,
            "lons": lons,
            "metadata": {
                "forecastTime": msg.forecastTime,
                "dataDate": msg.dataDate,
                "validDate": msg.validDate,
                "analysisTime": getattr(msg, "analDate", None),
            }
        }
    
    def extract_all_levels(
        self,
        file_path: str,
        var_code: str,
        region_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> List[Dict[str, Any]]:
        var_info = get_variable_info(var_code)
        if not var_info:
            return []
        
        level_values = var_info.get("level_values", [])
        results = []
        
        for level in level_values:
            result = self.extract_variable(file_path, var_code, level, region_bounds)
            if result:
                results.append(result)
        
        return results
    
    def extract_wind_components(
        self,
        file_path: str,
        level: int,
        region_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[Dict[str, Any]]:
        u_data = self.extract_variable(file_path, "u", level, region_bounds)
        v_data = self.extract_variable(file_path, "v", level, region_bounds)
        
        if not u_data or not v_data:
            return None
        
        u_vals = u_data["data"]
        v_vals = v_data["data"]
        
        speed = np.sqrt(u_vals**2 + v_vals**2)
        direction = np.degrees(np.arctan2(-u_vals, -v_vals))
        direction = np.where(direction < 0, direction + 360, direction)
        
        return {
            "variable_code": "wind",
            "level_type": "isobaricInhPa",
            "level": level,
            "unit": "m/s",
            "u_component": u_vals,
            "v_component": v_vals,
            "speed": speed,
            "direction": direction,
            "lats": u_data["lats"],
            "lons": u_data["lons"],
            "metadata": u_data["metadata"],
        }
    
    def extract_surface_wind(
        self,
        file_path: str,
        level: int,
        region_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[Dict[str, Any]]:
        u_data = self.extract_variable(file_path, "uSupe", level, region_bounds)
        v_data = self.extract_variable(file_path, "vSupe", level, region_bounds)
        
        if not u_data or not v_data:
            return None
        
        u_vals = u_data["data"]
        v_vals = v_data["data"]
        
        speed = np.sqrt(u_vals**2 + v_vals**2)
        direction = np.degrees(np.arctan2(-u_vals, -v_vals))
        direction = np.where(direction < 0, direction + 360, direction)
        
        return {
            "variable_code": "wind_surface",
            "level_type": "heightAboveGround",
            "level": level,
            "unit": "m/s",
            "u_component": u_vals,
            "v_component": v_vals,
            "speed": speed,
            "direction": direction,
            "lats": u_data["lats"],
            "lons": u_data["lons"],
            "metadata": u_data["metadata"],
        }
    
    def extract_pollution_data(
        self,
        file_path: str,
        region_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        pollution_vars = get_pollution_variables()
        results = {}
        
        for var_code in pollution_vars.keys():
            level_results = self.extract_all_levels(file_path, var_code, region_bounds)
            if level_results:
                results[var_code] = level_results
        
        return results

    def combine_wind_resultant(
        self,
        u_data: Dict[str, Any],
        v_data: Dict[str, Any],
        var_code: str = "vento",
        name: str = "Wind speed",
        unit: str = "m/s",
    ) -> Optional[Dict[str, Any]]:
        """Compute the wind resultant (magnitude = sqrt(u^2 + v^2)) from the
        already-extracted u/v components of the same level/region.

        The result reuses the grid, level type and metadata of the u component.
        """
        if u_data is None or v_data is None:
            return None
        u_vals = np.asarray(u_data["data"], dtype=float)
        v_vals = np.asarray(v_data["data"], dtype=float)
        if u_vals.size == 0 or v_vals.size == 0:
            return None

        speed = np.sqrt(u_vals**2 + v_vals**2)
        return {
            "variable_code": var_code,
            "variable_name": name,
            "level_type": u_data["level_type"],
            "level": u_data["level"],
            "unit": unit,
            "data": speed,
            "lats": u_data["lats"],
            "lons": u_data["lons"],
            "metadata": u_data["metadata"],
        }
    
    def compute_statistics(self, data: np.ndarray) -> Dict[str, float]:
        valid_data = data[~np.isnan(data)]
        if len(valid_data) == 0:
            return {"min": None, "max": None, "mean": None, "std": None, "count": 0}
        
        return {
            "min": float(np.min(valid_data)),
            "max": float(np.max(valid_data)),
            "mean": float(np.mean(valid_data)),
            "std": float(np.std(valid_data)),
            "count": int(len(valid_data)),
        }
    
    def data_to_matrix(self, data: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> Tuple[List[List[float]], List[float], List[float]]:
        unique_lats = np.unique(lats)
        unique_lons = np.unique(lons)
        
        matrix = data.reshape(len(unique_lats), len(unique_lons))
        
        return matrix.tolist(), unique_lats.tolist(), unique_lons.tolist()

def find_best_level(available_levels: List[int], target_level: int) -> int:
    if not available_levels:
        return target_level
    
    if target_level in available_levels:
        return target_level
    
    return min(available_levels, key=lambda x: abs(x - target_level))