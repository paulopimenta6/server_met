#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate legacy METAR data to new structure
"""
import json
import shutil
from pathlib import Path

SRC_DIR = Path("/home/paulo/Documentos/meus_codigos/server_met/METARpy")
DST_DIR = Path("/home/paulo/Documentos/meus_codigos/server_met/data/metar")

# Brazilian aviation stations
STATIONS = {
    "SBGR": {"name": "São Paulo/Guarulhos", "city": "São Paulo", "state": "SP"},
    "SBGL": {"name": "Rio de Janeiro/Galeão", "city": "Rio de Janeiro", "state": "RJ"},
    "SBBR": {"name": "Brasília", "city": "Brasília", "state": "DF"},
    "SBCF": {"name": "Belo Horizonte/Confins", "city": "Belo Horizonte", "state": "MG"},
    "SBPA": {"name": "Porto Alegre", "city": "Porto Alegre", "state": "RS"},
    "SBCT": {"name": "Curitiba", "city": "Curitiba", "state": "PR"},
    "SBBE": {"name": "Belém", "city": "Belém", "state": "PA"},
    "SBEG": {"name": "Manaus", "city": "Manaus", "state": "AM"},
    "SBRF": {"name": "Recife", "city": "Recife", "state": "PE"},
    "SBFZ": {"name": "Fortaleza", "city": "Fortaleza", "state": "CE"},
    "SBKP": {"name": "Campinas/Viracopos", "city": "Campinas", "state": "SP"},
    "SBFL": {"name": "Florianópolis", "city": "Florianópolis", "state": "SC"},
    "SBSV": {"name": "Salvador", "city": "Salvador", "state": "BA"},
    "SBGO": {"name": "Goiânia", "city": "Goiânia", "state": "GO"},
    "SBVT": {"name": "Vitória", "city": "Vitória", "state": "ES"},
}

def migrate():
    total_files = 0
    total_stations = 0
    
    for date_dir in sorted(SRC_DIR.iterdir()):
        if not date_dir.is_dir() or not date_dir.name.isdigit():
            continue
            
        date_str = date_dir.name
        print(f"Processing {date_str}...")
        
        for metar_file in date_dir.glob("*.json"):
            try:
                with open(metar_file) as f:
                    data = json.load(f)
                
                if "data" not in data or not data["data"]:
                    continue
                    
                metar_entry = data["data"][0]
                station_code = metar_entry.get("id_localidade ", "").strip()
                time_str = metar_entry.get("data ", "").strip()
                raw_metar = metar_entry.get("mens ", "").strip()
                
                if not station_code or not time_str or not raw_metar:
                    continue
                
                if station_code not in STATIONS:
                    continue
                
                # Create destination directory
                station_dir = Path("/home/paulo/Documentos/meus_codigos/server_met/data/metar") / station_code
                station_dir.mkdir(parents=True, exist_ok=True)
                
                # Create new filename: {station}{YYYYMMDDHHMM}.json
                new_filename = f"{station_code}{time_str}.json"
                dst_file = station_dir / new_filename
                
                # Parse time for display
                if len(time_str) >= 10:
                    display_time = f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]} {time_str[8:10]}:{time_str[10:12]}Z"
                else:
                    display_time = time_str
                
                # Create new format
                new_data = {
                    "station": station_code,
                    "station_info": STATIONS.get(station_code, {}),
                    "time": display_time,
                    "metar": raw_metar,
                    "raw": raw_metar
                }
                
                with open(dst_file, 'w') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                
                total_files += 1
                
            except Exception as e:
                print(f"Error processing {metar_file}: {e}")
    
    print(f"\nMigration complete: {total_files} files migrated")

if __name__ == "__main__":
    migrate()