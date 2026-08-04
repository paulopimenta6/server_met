#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health check endpoints - Server MET v2.0
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from api.schemas import HealthResponse
from core.persistence import persistence

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthResponse)
async def health_check():
    try:
        with persistence._get_connection() as conn:
            conn.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow(),
        database=db_status,
        api="running"
    )

@router.get("/ready")
async def readiness_check():
    return {"status": "ready"}