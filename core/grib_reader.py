#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leitor de arquivos GRIB usando pygrib - Server MET v2.0
Refatorado de leitura_dados_grib_MET.py
"""
import pygrib
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GribReader:
    # GFS uses different long names for the same variable at different levels
    # (e.g. "U component of wind" vs "10 metre U wind component"). Aliases let
    # us match by shortName as well.
    NAME_ALIASES = {
        "u component of wind": ["u", "10u", "ugrd"],
        "v component of wind": ["v", "10v", "vgrd"],
    }

    def __init__(self, grib_dir: Path):
        self.grib_dir = grib_dir
        self._grb_cache: Dict[str, Any] = {}
    
    def list_available_files(self, date_str: str) -> List[Path]:
        date_dir = self.grib_dir / date_str
        if not date_dir.exists():
            return []
        
        files = []
        for analysis in ["00", "06", "12", "18"]:
            ana_dir = date_dir / analysis
            if ana_dir.exists():
                for f in ana_dir.glob("gfs.t*z.pgrb2.*.f*"):
                    files.append(f)
        return sorted(files)
    
    def open_grib(self, file_path: Path) -> Optional[Any]:
        if str(file_path) in self._grb_cache:
            return self._grb_cache[str(file_path)]
        
        try:
            grb = pygrib.open(str(file_path))
            self._grb_cache[str(file_path)] = grb
            return grb
        except Exception as e:
            logger.error(f"Failed to open GRIB {file_path}: {e}")
            return None
    
    def get_messages(self, file_path: Path) -> List[Any]:
        grb = self.open_grib(file_path)
        if grb is None:
            return []
        return list(grb)
    
    def select_messages(
        self, 
        file_path: Path, 
        name: str = None,
        level_type: str = None,
        level: int = None,
        **kwargs
    ) -> List[Any]:
        grb = self.open_grib(file_path)
        if grb is None:
            return []
        
        select_kwargs = {}
        if name:
            select_kwargs["name"] = name
        if level_type:
            select_kwargs["typeOfLevel"] = level_type
        if level is not None:
            select_kwargs["level"] = level
        select_kwargs.update(kwargs)
        
        try:
            msgs = grb.select(**select_kwargs)
        except Exception:
            msgs = []
        
        if msgs or not name:
            return msgs
        
        # Exact-name select failed (GRIB name variants such as "10 metre U wind
        # component" vs "U component of wind"). Fall back to a tolerant match on
        # the long name (substring) and shortName aliases.
        aliases = self.NAME_ALIASES.get(name.lower(), [])
        return [
            m for m in grb
            if (name.lower() in m.name.lower()
                or getattr(m, "shortName", "").lower() in aliases)
            and (level_type is None or m.typeOfLevel == level_type)
            and (level is None or m.level == level)
        ]
    
    def get_available_variables(self, file_path: Path) -> List[Dict[str, Any]]:
        grb = self.open_grib(file_path)
        if grb is None:
            return []
        
        variables = []
        for msg in grb:
            variables.append({
                "name": msg.name,
                "shortName": getattr(msg, "shortName", ""),
                "level": msg.level,
                "typeOfLevel": msg.typeOfLevel,
                "units": msg.units,
                "parameterCategory": getattr(msg, "parameterCategory", None),
                "parameterNumber": getattr(msg, "parameterNumber", None),
                "forecastTime": msg.forecastTime,
                "dataDate": msg.dataDate,
                "validDate": msg.validDate,
            })
        return variables
    
    def find_pollution_variables(self, file_path: Path) -> List[Dict[str, Any]]:
        all_vars = self.get_available_variables(file_path)
        pollution_keywords = [
            "ozone", "nitrogen", "sulfur", "carbon monoxide", "pm2.5", "pm10",
            "aerosol", "dust", "mixing ratio", "chemical", "no2", "so2", "co"
        ]
        
        pollution_vars = []
        for var in all_vars:
            name_lower = var["name"].lower()
            if any(kw in name_lower for kw in pollution_keywords):
                pollution_vars.append(var)
        
        return pollution_vars
    
    def close_all(self):
        for grb in self._grb_cache.values():
            try:
                grb.close()
            except:
                pass
        self._grb_cache.clear()

class AutoGribReader(GribReader):
    def __init__(self, grib_dir: Path):
        super().__init__(grib_dir)
    
    def get_latest_analysis_files(self) -> List[Path]:
        date_dirs = sorted([d for d in self.grib_dir.iterdir() if d.is_dir()], reverse=True)
        if not date_dirs:
            return []
        
        latest_date = date_dirs[0]
        analysis_dirs = sorted([d for d in latest_date.iterdir() if d.is_dir()], reverse=True)
        
        files = []
        for ana_dir in analysis_dirs:
            for res in ["0p25", "1p00"]:
                for f in ana_dir.glob(f"gfs.t*{res}.f*"):
                    files.append(f)
        
        return sorted(files)

class ManualGribReader(GribReader):
    def __init__(self, grib_dir: Path, date_str: str, analysis: str):
        super().__init__(grib_dir)
        self.date_str = date_str
        self.analysis = analysis
    
    def get_forecast_files(self) -> List[Path]:
        date_dir = self.grib_dir / self.date_str
        ana_dir = date_dir / self.analysis
        if not ana_dir.exists():
            return []
        
        files = []
        for res in ["0p25", "1p00"]:
            for f in ana_dir.glob(f"gfs.t*{res}.f*"):
                files.append(f)
        return sorted(files)