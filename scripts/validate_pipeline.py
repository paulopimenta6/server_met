#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação do pipeline com dados reais - Server MET v2.0
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import GRIB_DIR, REGIOES
from core.downloader import GribDownloader
from core.grib_reader import AutoGribReader
from core.processor import DataProcessor
from core.persistence import persistence
from core.variables import get_meteorological_variables, get_pollution_variables

async def test_download():
    print("=" * 60)
    print("TESTE 1: Download de GRIBs")
    print("=" * 60)
    
    async with GribDownloader() as downloader:
        # Testar download do ciclo mais recente
        downloaded = await downloader.download_latest_cycle(resolutions=["0p25"])
        print(f"Arquivos baixados: {len(downloaded)}")
        for f in downloaded[:5]:
            print(f"  - {f}")
        return len(downloaded) > 0

def test_grib_reader():
    print("\n" + "=" * 60)
    print("TESTE 2: Leitura de GRIBs e descoberta de variáveis")
    print("=" * 60)
    
    reader = AutoGribReader(GRIB_DIR)
    files = reader.get_latest_analysis_files()
    
    if not files:
        print("Nenhum arquivo GRIB encontrado. Execute o download primeiro.")
        return False
    
    print(f"Arquivos encontrados: {len(files)}")
    
    # Inspecionar primeiro arquivo
    test_file = files[0]
    print(f"\nInspecionando: {test_file}")
    
    variables = reader.get_available_variables(test_file)
    print(f"Total de variáveis no arquivo: {len(variables)}")
    
    # Procurar variáveis de poluição
    pollution_vars = reader.find_pollution_variables(test_file)
    print(f"\nVariáveis de poluição/químicas encontradas: {len(pollution_vars)}")
    for v in pollution_vars[:10]:
        print(f"  - {v['name']} | level={v['level']} | typeOfLevel={v['typeOfLevel']} | units={v['units']}")
    
    return True

def test_processor():
    print("\n" + "=" * 60)
    print("TESTE 3: Processamento de variáveis")
    print("=" * 60)
    
    reader = AutoGribReader(GRIB_DIR)
    files = reader.get_latest_analysis_files()
    
    if not files:
        print("Nenhum arquivo GRIB encontrado.")
        return False
    
    processor = DataProcessor(reader)
    test_file = files[0]
    
    # Testar variável meteorológica
    print("\n--- Testando variável meteorológica (temp 1000 hPa) ---")
    region_bounds = REGIOES["SP"]
    bounds = (region_bounds["lon_min"], region_bounds["lon_max"], 
              region_bounds["lat_min"], region_bounds["lat_max"])
    
    result = processor.extract_variable(str(test_file), "temp", 1000, bounds)
    if result:
        stats = processor.compute_statistics(result["data"])
        print(f"  Sucesso! Shape: {result['data'].shape}")
        print(f"  Stats: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}")
    else:
        print("  Falha ao extrair temp")
    
    # Testar variável de vento
    print("\n--- Testando vento (1000 hPa) ---")
    wind = processor.extract_wind_components(str(test_file), 1000, bounds)
    if wind:
        stats = processor.compute_statistics(wind["speed"])
        print(f"  Sucesso! Shape: {wind['speed'].shape}")
        print(f"  Velocidade - min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}")
    else:
        print("  Falha ao extrair vento")
    
    # Testar poluição (O3)
    print("\n--- Testando ozônio (O3) ---")
    o3_result = processor.extract_variable(str(test_file), "o3", 500, bounds)
    if o3_result:
        stats = processor.compute_statistics(o3_result["data"])
        print(f"  Sucesso! Shape: {o3_result['data'].shape}")
        print(f"  Stats: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f} {o3_result['unit']}")
    else:
        print("  O3 não encontrado neste arquivo/nível")
    
    # Testar extração de todos os níveis de O3
    print("\n--- Testando todos os níveis de O3 ---")
    o3_all = processor.extract_all_levels(str(test_file), "o3", bounds)
    print(f"  Níveis extraídos: {len(o3_all)}")
    for r in o3_all[:5]:
        stats = processor.compute_statistics(r["data"])
        print(f"    {r['level']} hPa: min={stats['min']:.2f}, max={stats['max']:.2f} ppbv")
    
    return True

def test_persistence():
    print("\n" + "=" * 60)
    print("TESTE 4: Persistência (SQLite + CSV)")
    print("=" * 60)
    
    reader = AutoGribReader(GRIB_DIR)
    files = reader.get_latest_analysis_files()
    
    if not files:
        print("Nenhum arquivo GRIB encontrado.")
        return False
    
    processor = DataProcessor(reader)
    test_file = files[0]
    bounds = (REGIOES["SP"]["lon_min"], REGIOES["SP"]["lon_max"],
              REGIOES["SP"]["lat_min"], REGIOES["SP"]["lat_max"])
    
    # Extrair e persistir temp
    result = processor.extract_variable(str(test_file), "temp", 1000, bounds)
    if result:
        matrix, lats, lons = processor.data_to_matrix(result["data"], result["lats"], result["lons"])
        stats = processor.compute_statistics(result["data"])
        
        grib_id = persistence.save_grib_metadata(
            file_path=str(test_file),
            analysis_time=test_file.parent.name,
            forecast_hour=int(test_file.stem.split("f")[-1]),
            data_date=test_file.parent.parent.name,
            resolution="0p25" if "0p25" in str(test_file) else "1p00"
        )
        print(f"GRIB metadata salvo com ID: {grib_id}")
        
        persist_id = persistence.save_processed_data(
            grib_metadata_id=grib_id,
            variable_code="temp",
            level_type=result["level_type"],
            level_value=1000,
            region_code="SP",
            min_value=stats["min"],
            max_value=stats["max"],
            mean_value=stats["mean"],
            data_matrix=matrix,
            lats=lats,
            lons=lons
        )
        print(f"Dados processados salvos com ID: {persist_id}")
        
        # Consultar
        queried = persistence.query_data(variable_code="temp", region_code="SP", limit=5)
        print(f"Consulta retornou {len(queried)} registros")
        
        # Verificar CSV
        if queried and queried[0]["csv_path"]:
            import os
            csv_path = queried[0]["csv_path"]
            if os.path.exists(csv_path):
                print(f"CSV gerado: {csv_path} ({os.path.getsize(csv_path)} bytes)")
            else:
                print(f"CSV não encontrado: {csv_path}")
        
        return True
    return False

def test_api_endpoints():
    print("\n" + "=" * 60)
    print("TESTE 5: Endpoints da API (requer servidor rodando)")
    print("=" * 60)
    
    import httpx
    
    try:
        with httpx.Client(base_url="http://localhost:8000", timeout=10) as client:
            # Health
            r = client.get("/health")
            print(f"  Health: {r.status_code} - {r.json()['status']}")
            
            # Variables
            r = client.get("/api/v1/data/variables")
            vars = r.json()["variables"]
            print(f"  Variables: {len(vars)} variáveis disponíveis")
            
            # Regions
            r = client.get("/api/v1/data/regions")
            regions = r.json()["regions"]
            print(f"  Regions: {len(regions)} regiões disponíveis")
            
            # Available
            r = client.get("/api/v1/data/available")
            avail = r.json()
            print(f"  Available: {len(avail['variables'])} vars, {len(avail['regions'])} regions, {len(avail['dates'])} dates")
            
            # Query data
            r = client.get("/api/v1/data/", params={"variable": "temp", "level": 1000, "region": "SP", "limit": 3})
            data = r.json()
            print(f"  Query data: {data['total']} resultados")
            
        return True
    except Exception as e:
        print(f"  API não acessível: {e}")
        return False

async def main():
    print("🧪 VALIDAÇÃO END-TO-END DO SERVER MET v2.0")
    print("=" * 60)
    
    results = {}
    
    # Teste 1: Download
    try:
        results["download"] = await test_download()
    except Exception as e:
        print(f"Erro no download: {e}")
        results["download"] = False
    
    # Teste 2: GRIB Reader
    try:
        results["grib_reader"] = test_grib_reader()
    except Exception as e:
        print(f"Erro no GRIB reader: {e}")
        results["grib_reader"] = False
    
    # Teste 3: Processor
    try:
        results["processor"] = test_processor()
    except Exception as e:
        print(f"Erro no processor: {e}")
        results["processor"] = False
    
    # Teste 4: Persistence
    try:
        results["persistence"] = test_persistence()
    except Exception as e:
        print(f"Erro na persistência: {e}")
        results["persistence"] = False
    
    # Teste 5: API
    try:
        results["api"] = test_api_endpoints()
    except Exception as e:
        print(f"Erro na API: {e}")
        results["api"] = False
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    for test, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test}: {status}")
    
    all_passed = all(results.values())
    print(f"\n{'🎉 TODOS OS TESTES PASSARAM!' if all_passed else '⚠️ ALGUNS TESTES FALHARAM'}")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())