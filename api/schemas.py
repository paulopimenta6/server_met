#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic schemas for API - Server MET v2.0
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class VariableInfo(BaseModel):
    code: str
    name: str
    level_type: str
    level_values: List[int]
    unit: str
    description: str
    category: str

class RegionInfo(BaseModel):
    code: str
    name: str
    bounds: Dict[str, float]

class DataQueryParams(BaseModel):
    variable: Optional[str] = None
    level: Optional[int] = None
    region: Optional[str] = None
    date: Optional[str] = None
    analysis: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=10000)

class ProcessedDataResponse(BaseModel):
    id: int
    grib_metadata_id: int
    variable_code: str
    level_type: str
    level_value: int
    region_code: str
    min_value: Optional[float]
    max_value: Optional[float]
    mean_value: Optional[float]
    csv_path: Optional[str]
    created_at: datetime
    file_path: Optional[str] = None
    analysis_time: Optional[str] = None
    forecast_hour: Optional[int] = None
    data_date: Optional[str] = None
    resolution: Optional[str] = None

class DataListResponse(BaseModel):
    total: int
    data: List[ProcessedDataResponse]

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database: str
    api: str

class VariableListResponse(BaseModel):
    variables: List[VariableInfo]

class RegionListResponse(BaseModel):
    regions: List[RegionInfo]

class StatsResponse(BaseModel):
    variable: str
    level: int
    region: str
    date: str
    analysis: str
    min: float
    max: float
    mean: float
    count: int

class ExportRequest(BaseModel):
    variable: str
    level: int
    region: str
    date: Optional[str] = None
    analysis: Optional[str] = None