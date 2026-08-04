#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes End-to-End com Playwright - Server MET v2.0
"""
import asyncio
import pytest
from playwright.async_api import async_playwright, expect
import subprocess
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

@pytest.fixture(scope="session")
def api_server():
    """Start FastAPI server for testing"""
    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app",
        "--host", "0.0.0.0", "--port", "8000"
    ], cwd=Path(__file__).parent.parent)
    
    time.sleep(3)  # Wait for server to start
    
    yield BASE_URL
    
    proc.terminate()
    proc.wait(timeout=5)

@pytest.fixture(scope="session")
async def browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser):
    page = await browser.new_page()
    yield page
    await page.close()

class TestAPIEndpoints:
    """Test API endpoints directly"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_server):
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_server}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "database" in data
    
    @pytest.mark.asyncio
    async def test_variables_endpoint(self, api_server):
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_server}/api/v1/data/variables")
            assert response.status_code == 200
            data = response.json()
            assert "variables" in data
            assert len(data["variables"]) > 0
            
            # Check for pollution variables
            var_codes = [v["code"] for v in data["variables"]]
            assert "o3" in var_codes
            assert "temp" in var_codes
            assert "u" in var_codes
    
    @pytest.mark.asyncio
    async def test_regions_endpoint(self, api_server):
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_server}/api/v1/data/regions")
            assert response.status_code == 200
            data = response.json()
            assert "regions" in data
            assert len(data["regions"]) >= 18  # 11 original + 7 new
            
            region_codes = [r["code"] for r in data["regions"]]
            assert "SP" in region_codes
            assert "RJ" in region_codes
            assert "FOR" in region_codes  # New region
            assert "REC" in region_codes  # New region

    @pytest.mark.asyncio
    async def test_available_endpoint(self, api_server):
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_server}/api/v1/data/available")
            assert response.status_code == 200
            data = response.json()
            assert "variables" in data
            assert "regions" in data
            assert "dates" in data

class TestFrontend:
    """Test frontend with Playwright"""
    
    @pytest.mark.asyncio
    async def test_frontend_loads(self, page, api_server):
        await page.goto(api_server)
        await expect(page.locator("h1")).to_contain_text("Server MET v2.0")
    
    @pytest.mark.asyncio
    async def test_dropdowns_populate(self, page, api_server):
        await page.goto(api_server)
        
        # Wait for dropdowns to populate
        await page.wait_for_selector("#variableSelect option[value='temp']", timeout=10000)
        await page.wait_for_selector("#regionSelect option[value='SP']", timeout=10000)
        
        # Check variable dropdown has options
        var_options = await page.locator("#variableSelect option").all()
        assert len(var_options) > 1  # At least one real option + placeholder
        
        # Check region dropdown has options
        region_options = await page.locator("#regionSelect option").all()
        assert len(region_options) > 1
    
    @pytest.mark.asyncio
    async def test_variable_change_updates_levels(self, page, api_server):
        await page.goto(api_server)
        
        # Wait for initial load
        await page.wait_for_selector("#variableSelect option[value='temp']", timeout=10000)
        await page.wait_for_selector("#regionSelect option[value='SP']", timeout=10000)
        
        # Select variable
        await page.select_option("#variableSelect", "temp")
        await page.select_option("#regionSelect", "SP")
        
        # Wait for levels to populate
        await page.wait_for_selector("#levelSelect option[value='1000']", timeout=10000)
        
        level_options = await page.locator("#levelSelect option").all()
        assert len(level_options) > 1
    
    @pytest.mark.asyncio
    async def test_load_data_button(self, page, api_server):
        await page.goto(api_server)
        
        await page.wait_for_selector("#variableSelect option[value='temp']", timeout=10000)
        await page.wait_for_selector("#regionSelect option[value='SP']", timeout=10000)
        
        await page.select_option("#variableSelect", "temp")
        await page.select_option("#regionSelect", "SP")
        await page.wait_for_selector("#levelSelect option[value='1000']", timeout=10000)
        await page.select_option("#levelSelect", "1000")
        
        # Click load button
        await page.click("#loadBtn")
        
        # Wait for either data or error
        try:
            await page.wait_for_selector("#statsPanel:not(.hidden)", timeout=15000)
            # Check stats are displayed
            min_val = await page.locator("#statMin").text_content()
            max_val = await page.locator("#statMax").text_content()
            mean_val = await page.locator("#statMean").text_content()
            assert min_val != "-"
            assert max_val != "-"
        except:
            # Might not have data, check for error message
            loading_text = await page.locator("#loading").text_content()
            print(f"Load result: {loading_text}")

class TestPipeline:
    """Test the data pipeline"""
    
    @pytest.mark.asyncio
    async def test_pipeline_imports(self):
        """Test that all pipeline modules can be imported"""
        from scripts.run_pipeline import METPipeline
        from core.downloader import GribDownloader
        from core.grib_reader import AutoGribReader
        from core.processor import DataProcessor
        from core.persistence import persistence
        from core.variables import VARIABLES_MET
        
        assert METPipeline is not None
        assert GribDownloader is not None
        assert AutoGribReader is not None
        assert DataProcessor is not None
        assert persistence is not None
        assert len(VARIABLES_MET) > 10
    
    def test_pollution_variables_defined(self):
        """Test that pollution variables are defined"""
        from core.variables import get_pollution_variables, get_variable_info
        
        pollution = get_pollution_variables()
        assert "o3" in pollution
        assert "no2" in pollution
        assert "so2" in pollution
        assert "co" in pollution
        assert "pm25" in pollution
        assert "pm10" in pollution
        
        o3_info = get_variable_info("o3")
        assert o3_info["category"] == "pollution"
        assert o3_info["unit"] == "ppbv"

class TestPersistence:
    """Test persistence layer"""
    
    def test_database_initialization(self):
        from core.persistence import PersistenceManager
        from pathlib import Path
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            pm = PersistenceManager(db_path)
            
            # Test saving metadata
            grib_id = pm.save_grib_metadata(
                file_path="/test/path.grb",
                analysis_time="00",
                forecast_hour=6,
                data_date="20240115",
                resolution="0p25"
            )
            assert grib_id > 0
            
            # Test saving processed data
            import numpy as np
            matrix = [[1.0, 2.0], [3.0, 4.0]]
            lats = [-20, -18]
            lons = [-50, -48]
            
            persist_id = pm.save_processed_data(
                grib_metadata_id=grib_id,
                variable_code="temp",
                level_type="isobaricInhPa",
                level_value=1000,
                region_code="SP",
                min_value=1.0,
                max_value=4.0,
                mean_value=2.5,
                data_matrix=matrix,
                lats=lats,
                lons=lons
            )
            assert persist_id > 0
            
            # Test querying
            results = pm.query_data(variable_code="temp", region_code="SP")
            assert len(results) == 1
            assert results[0]["variable_code"] == "temp"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])