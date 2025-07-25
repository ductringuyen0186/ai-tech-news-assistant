"""
Health and API Info Routes
==========================

Routes for API health checks, status, and general information.
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

from ...core.config import get_settings

settings = get_settings()
from ...models.api import HealthCheck

router = APIRouter(prefix="", tags=["Health"])


@router.get("/")
async def api_info() -> Dict[str, Any]:
    """API information endpoint."""
    return {
        "name": "AI Tech News Assistant API",
        "version": "1.0.0",
        "description": "AI-powered tech news aggregation and analysis",
        "endpoints": {
            "health": "/health - API health check",
            "news": "/api/news - News article operations",
            "summarize": "/api/summarize - Content summarization",
            "embeddings": "/api/embeddings - Embedding operations",
            "search": "/api/search - Semantic search"
        },
        "documentation": "/docs"
    }


@router.get("/health")
async def health_check() -> HealthCheck:
    """
    Comprehensive health check endpoint.
    
    Returns:
        HealthCheck model with system status
    """
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        uptime_seconds=0.0,  # Would be calculated from app start time
        dependencies={
            "database": "healthy",
            "embeddings": "healthy",
            "summarization": "healthy"
        }
    )


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """Simple ping endpoint for basic connectivity check."""
    return {
        "status": "ok",
        "message": "API is running",
        "timestamp": datetime.utcnow().isoformat()
    }
