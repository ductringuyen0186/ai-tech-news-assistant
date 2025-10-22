"""
Ingestion Routes
===============

API endpoints for managing news article ingestion:
- POST /api/ingest - Trigger manual ingestion
- GET /api/ingest/status - Get latest ingestion status
- GET /api/ingest/stats - Get ingestion statistics
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Body
from pydantic import BaseModel

from src.database.base import get_db
from src.database.session import DatabaseManager
from src.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

# Store latest ingestion result globally (in production, use Redis or database)
latest_ingestion_result = None


class IngestRequest(BaseModel):
    """Request model for ingestion endpoint."""
    sources: Optional[List[Dict[str, str]]] = None
    background: bool = True


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint."""
    message: str
    job_id: Optional[str] = None
    background: bool


class IngestStatusResponse(BaseModel):
    """Response model for ingestion status endpoint."""
    status: str
    result: Optional[Dict[str, Any]] = None


@router.post("/", response_model=IngestResponse)
async def trigger_ingestion(
    request: IngestRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    db=Depends(get_db)
):
    """
    Trigger news article ingestion from configured RSS feeds.
    
    Can run in foreground or background based on request.
    
    Args:
        request: IngestRequest with optional custom sources
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        IngestResponse with job information
        
    Raises:
        HTTPException: 500 if ingestion fails
    """
    try:
        ingestion_service = IngestionService(db)
        
        if request.background and background_tasks:
            # Run in background
            background_tasks.add_task(
                _run_ingestion,
                ingestion_service,
                request.sources
            )
            return IngestResponse(
                message="Ingestion started in background",
                job_id="bg_ingest_001",
                background=True
            )
        else:
            # Run in foreground
            result = ingestion_service.ingest_all(request.sources)
            ingestion_service.close()
            
            global latest_ingestion_result
            latest_ingestion_result = result
            
            return IngestResponse(
                message=f"Ingestion completed: {result.total_articles_saved} articles saved",
                background=False
            )
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/status", response_model=IngestStatusResponse)
async def get_ingestion_status():
    """
    Get the status of the latest ingestion operation.
    
    Returns:
        IngestStatusResponse with latest ingestion result
    """
    global latest_ingestion_result
    
    if latest_ingestion_result is None:
        return IngestStatusResponse(
            status="no_ingestion_run",
            result=None
        )
    
    return IngestStatusResponse(
        status=latest_ingestion_result.status.value,
        result=latest_ingestion_result.to_dict()
    )


@router.get("/stats")
async def get_ingestion_stats(db=Depends(get_db)):
    """
    Get ingestion statistics and database metrics.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with statistics about articles, sources, and categories
    """
    try:
        ingestion_service = IngestionService(db)
        stats = ingestion_service.get_stats()
        ingestion_service.close()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


def _run_ingestion(service: IngestionService, sources: Optional[List[Dict[str, str]]]):
    """
    Background task for running ingestion.
    
    Args:
        service: IngestionService instance
        sources: Optional custom sources
    """
    global latest_ingestion_result
    
    try:
        result = service.ingest_all(sources)
        latest_ingestion_result = result
        logger.info(f"Background ingestion completed: {result.to_dict()}")
    except Exception as e:
        logger.error(f"Background ingestion failed: {e}", exc_info=True)
    finally:
        service.close()

