#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate pre-rendered PNG maps for the image-based frontend
"""
import os
import sys
sys.path.insert(0, '/home/paulo/Documentos/meus_codigos/server_met')

from core.grib_reader import AutoGribReader
from core.processor import DataProcessor
from core.config import REGIOES
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

MAPS_DIR = Path('/home/paulo/Documentos/meus_codigos/server_met/maps')
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# Variables that have isobaric levels
ISOBARIC_VARIABLES = {
    'temp': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'RdBu_r', 'unit': '°C'},
    'umidadeRel': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'Blues', 'unit': '%'},
    'nuvem': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'Greys', 'unit': '%'},
    'u': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'RdBu', 'unit': 'm/s'},
    'v': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'RdBu', 'unit': 'm/s'},
    'o3': {'levels': [1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10], 'cmap': 'OrRd', 'unit': 'ppbv'},
}

# Surface variables
SURFACE_VARIABLES = {
    'ps': {'cmap': 'YlOrRd', 'unit': 'hPa'},
    'prnm': {'cmap': 'YlOrRd', 'unit': 'hPa'},
    'temps': {'cmap': 'RdBu_r', 'unit': '°C'},
    'chuvaNaoConvec': {'cmap': 'Blues', 'unit': 'mm'},
    'chuvaConvec': {'cmap': 'Blues', 'unit': 'mm'},
    'pm25': {'cmap': 'OrRd', 'unit': 'µg/m³'},
    'pm10': {'cmap': 'OrRd', 'unit': 'µg/m³'},
    'aod': {'cmap': 'YlOrBr', 'unit': ''},
}

def generate_map(data, lats, lons, variable, level, region, cmap, unit, date_str, analysis, forecast):
    """Generate a PNG map from data matrix"""
    lats = np.array(lats)
    lons = np.array(lons)
    data = np.array(data)
    
    # Create 2D coordinate grids
    lon_2d, lat_2d = np.meshgrid(lons, lats)
    
    lon_min, lon_max = lons.min(), lons.max()
    lat_min, lat_max = lats.min(), lats.max()
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create basemap
    m = Basemap(projection='mill',
                llcrnrlat=lat_min,
                urcrnrlat=lat_max,
                llcrnrlon=lon_min,
                urcrnrlon=lon_max,
                resolution='i')
    
    # Convert coordinates
    x, y = m(lon_2d, lat_2d)
    
    # Plot data
    vmin, vmax = np.nanmin(data), np.nanmax(data)
    cs = m.contourf(x, y, data, levels=30, cmap=cmap, vmin=vmin, vmax=vmax)
    
    # Add map features
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries(linewidth=0.3)
    m.drawstates(linewidth=0.2)
    
    # Add colorbar
    cbar = plt.colorbar(cs, orientation='horizontal', pad=0.05, shrink=0.8)
    cbar.set_label(unit)
    
    # Title
    level_str = f"{variable.upper()} - {level} hPa" if level > 0 else f"{variable.upper()} - Superfície"
    plt.title(f"GFS 0.25° - {region} - {level_str}\nData: {date_str} Análise: {analysis}Z Previsão: {forecast}h", fontsize=10)
    
    # Save
    level_str_file = str(level) if level > 0 else 'SFC'
    filename = f"GFS_0p25_{region.upper()}_N{level_str_file}_{variable}_{analysis}_{date_str}_{forecast}.png"
    filepath = MAPS_DIR / filename
    plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    return filepath

def main():
    print("=== Generating pre-rendered maps ===")
    
    # Initialize
    reader = AutoGribReader(Path('/home/paulo/Documentos/meus_codigos/server_met/data/grib'))
    processor = DataProcessor(reader)
    
    # Get available GRIB files
    files = reader.get_latest_analysis_files()
    print(f"Found {len(files)} GRIB files")
    
    # Test regions to process (just a few for now)
    test_regions = ['SP', 'RJ', 'AM']
    
    for file_path in files:
        # Skip f000 files (analysis only, no isobaric data)
        if 'f000' in file_path.name:
            print(f"Skipping analysis file: {file_path.name}")
            continue
            
        print(f"Processing {file_path.name}...")
        
        # Parse filename for metadata
        parts = file_path.stem.split('.')
        analysis = parts[1][1:3]  # 00 from t00z
        forecast = parts[-1][1:]  # 003 from f003
        date_str = file_path.parent.parent.name  # 20260804
        
        # Process each region
        for region_code in test_regions:
            if region_code not in REGIOES:
                continue
            bounds = REGIOES[region_code]
            region_bounds = (bounds['lon_min'], bounds['lon_max'], bounds['lat_min'], bounds['lat_max'])
            
            # Process isobaric variables
            for var_name, var_info in ISOBARIC_VARIABLES.items():
                for level in var_info['levels']:
                    try:
                        result = processor.extract_variable(str(file_path), var_name, level, region_bounds)
                        if result and result['data'].size > 0:
                            matrix, lats, lons = processor.data_to_matrix(result['data'], result['lats'], result['lons'])
                            if len(matrix) > 0 and len(matrix[0]) > 0:
                                generate_map(np.array(matrix), lats, lons, var_name, level, region_code, var_info['cmap'], var_info['unit'],
                                           date_str, analysis, forecast)
                                print(f"  Generated: {region_code} {var_name} {level}hPa")
                    except Exception as e:
                        pass
            
            # Process surface variables
            for var_name, var_info in SURFACE_VARIABLES.items():
                try:
                    result = processor.extract_variable(str(file_path), var_name, None, region_bounds)
                    if result and result['data'].size > 0:
                        matrix, lats, lons = processor.data_to_matrix(result['data'], result['lats'], result['lons'])
                        if len(matrix) > 0 and len(matrix[0]) > 0:
                            generate_map(np.array(matrix), lats, lons, var_name, 0, region_code, var_info['cmap'], var_info['unit'],
                                       date_str, analysis, forecast)
                            print(f"  Generated: {region_code} {var_name} SFC")
                except Exception as e:
                    pass

    print("\n=== Map generation complete ===")

if __name__ == "__main__":
    import numpy as np
    main()