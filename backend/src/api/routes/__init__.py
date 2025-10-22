"""
API Routes Package
================

Main router that combines all route modules for the AI Tech News Assistant API.
Provides a clean, organized structure for API endpoints with proper tagging
and documentation.
"""

from fastapi import APIRouter

from .health import router as health_router
from .news import router as news_router
from .summarization import router as summarization_router
from .embeddings import router as embeddings_router
from .search import router as search_router
from .ingestion import router as ingestion_router

# Create the main API router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(news_router)
api_router.include_router(summarization_router)
api_router.include_router(embeddings_router)
api_router.include_router(search_router)
api_router.include_router(ingestion_router)

# Create a separate router for health/root endpoints (no /api prefix)
root_router = APIRouter()
root_router.include_router(health_router)

__all__ = ["api_router", "root_router"]
