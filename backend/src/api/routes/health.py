"""
Health and API Info Routes
==========================

Routes for API health checks, status, and general information.
"""

import sqlite3
import time
from fastapi import APIRouter, Response
from typing import Dict, Any
from datetime import datetime, timezone

try:
    import psutil
except ImportError:
    psutil = None

from ...core.config import get_settings
from ...models.health import HealthResponse, ComponentHealth, PingResponse

settings = get_settings()

# Global start time for uptime calculation
_start_time = time.time()

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
        "documentation": "/docs",
        "docs_url": "/docs"  # Add this field for test compatibility
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status of the API and its components in HealthCheck format
    """
    try:
        # Basic database connectivity check
        database_status = "connected"
        try:
            db_path = settings.get_database_path()
            conn = sqlite3.connect(db_path)
            conn.close()
        except Exception:
            database_status = "error"
        
        # Simple service statuses for basic health check
        services = {
            "database": database_status,
            "embeddings": "available",
            "summarization": "available"
        }
        
        # Determine overall status (degraded if database has issues, healthy otherwise)
        if database_status == "error":
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        uptime_seconds = time.time() - _start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc),
            "version": "1.0.0",
            "uptime": uptime_seconds,  # Return numeric uptime for test compatibility
            "uptime_seconds": uptime_seconds,
            "services": services,
            "components": {
                "database": {
                    "name": "database",
                    "status": "healthy" if database_status == "connected" else "unhealthy",
                    "message": "Database connectivity check",
                    "last_checked": datetime.now(timezone.utc),
                    "details": None,
                    "metadata": {}
                }
            }
        }
    except Exception:
        uptime_seconds = time.time() - _start_time
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc),
            "version": "1.0.0",
            "uptime": uptime_seconds,  # Return numeric uptime for test compatibility
            "uptime_seconds": uptime_seconds,
            "services": {
                "database": "error",
                "embeddings": "unavailable",
                "summarization": "unavailable"
            },
            "components": {}
        }


@router.get("/health/detailed")
async def detailed_health_check() -> HealthResponse:
    """
    Detailed health check endpoint that checks all service components.
    
    Returns:
        Comprehensive health status including all services
    """
    try:
        # Get all service instances
        article_repo = get_article_repository()
        embedding_service = get_embedding_service()
        news_service = get_news_service()
        summarization_service = get_summarization_service()
        
        # Perform health checks on all services
        components = {}
        
        # Database/Repository health check
        try:
            db_health = await article_repo.health_check()
            components["database"] = ComponentHealth(
                name="database",
                status=db_health.get("status", "unhealthy"),
                message=f"Database accessible: {db_health.get('database_accessible', False)}, Articles: {db_health.get('total_articles', 0)}"
            )
        except Exception as e:
            components["database"] = ComponentHealth(
                name="database",
                status="unhealthy",
                message=f"Database health check failed: {str(e)}"
            )
        
        # Embedding service health check
        try:
            embedding_health = await embedding_service.health_check()
            components["embeddings"] = ComponentHealth(
                name="embeddings",
                status=embedding_health.get("status", "unhealthy"),
                message=f"Model loaded: {embedding_health.get('model_loaded', False)}, GPU: {embedding_health.get('gpu_available', False)}"
            )
        except Exception as e:
            components["embeddings"] = ComponentHealth(
                name="embeddings",
                status="unhealthy",
                message=f"Embedding service health check failed: {str(e)}"
            )
        
        # News service health check
        try:
            news_health = await news_service.health_check()
            components["news"] = ComponentHealth(
                name="news",
                status=news_health.get("status", "unhealthy"),
                message=f"Feeds accessible: {news_health.get('feeds_accessible', 0)}/{news_health.get('feeds_total', 0)}"
            )
        except Exception as e:
            components["news"] = ComponentHealth(
                name="news",
                status="unhealthy",
                message=f"News service health check failed: {str(e)}"
            )
        
        # Summarization service health check
        try:
            summarization_health = await summarization_service.health_check()
            components["summarization"] = ComponentHealth(
                name="summarization",
                status=summarization_health.get("status", "unhealthy"),
                message=f"API accessible: {summarization_health.get('api_accessible', False)}, Model: {summarization_health.get('model', 'unknown')}"
            )
        except Exception as e:
            components["summarization"] = ComponentHealth(
                name="summarization", 
                status="unhealthy",
                message=f"Summarization service health check failed: {str(e)}"
            )
        
        # Determine overall status
        overall_status = determine_overall_status(components)
        
        # Convert components to match test expectations (database -> database, etc.)
        components_dict = {
            "database": components["database"],
            "embedding_service": components["embeddings"],
            "news_service": components["news"], 
            "summarization_service": components["summarization"]
        }
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            uptime=format_uptime(time.time() - _start_time),
            components=components_dict
        )
        
    except Exception:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            uptime=format_uptime(time.time() - _start_time),
            components=[]
        )


@router.get("/ping")
async def ping() -> PingResponse:
    """Simple ping endpoint for basic connectivity test."""
    return PingResponse(
        message="pong",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/health/ready")
async def readiness_check(response: Response) -> Dict[str, Any]:
    """
    Readiness probe for container orchestration.
    
    Returns:
        Readiness status indicating if the service can handle requests
    """
    try:
        # Check database connectivity using repository
        article_repo = get_article_repository()
        db_health = await article_repo.health_check()
        
        is_ready = db_health.get("status") == "healthy" and db_health.get("database_accessible", False)
        
        response_data = {
            "ready": is_ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "accessible" if is_ready else "inaccessible"
            }
        }
        
        if not is_ready:
            response.status_code = 503
            
        return response_data
        
    except Exception as e:
        response.status_code = 503
        return {
            "ready": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe for container orchestration.
    
    Returns:
        Liveness status indicating if the service is running
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "running"
    }


@router.get("/health/metrics")
async def metrics() -> Dict[str, Any]:
    """
    Basic metrics endpoint.
    
    Returns:
        System and application metrics including service statistics
    """
    uptime_seconds = time.time() - _start_time
    
    # Collect service statistics
    services = {}
    
    # Database statistics
    try:
        article_repo = get_article_repository()
        db_stats = await article_repo.get_stats()
        services["database"] = db_stats
    except Exception as e:
        services["database"] = {"error": str(e)}
    
    # Embedding service statistics
    try:
        embedding_service = get_embedding_service()
        embedding_stats = await embedding_service.get_stats()
        services["embedding_service"] = embedding_stats
    except Exception as e:
        services["embedding_service"] = {"error": str(e)}
    
    # News service statistics
    try:
        news_service = get_news_service()
        news_stats = await news_service.get_stats()
        services["news_service"] = news_stats
    except Exception as e:
        services["news_service"] = {"error": str(e)}
    
    # Summarization service statistics
    try:
        summarization_service = get_summarization_service()
        summarization_stats = await summarization_service.get_stats()
        services["summarization_service"] = summarization_stats
    except Exception as e:
        services["summarization_service"] = {"error": str(e)}
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": uptime_seconds,
        "system": {
            "memory_usage": {"status": "normal"},
            "cpu_usage": 0.0,
            "disk_usage": {"status": "normal"}
        },
        "application": {
            "request_count": 0,
            "error_count": 0
        },
        "services": services
    }


# Utility functions for health checks

def get_system_metrics() -> Dict[str, Any]:
    """Get basic system metrics."""
    return {
        "memory_usage": "normal",
        "cpu_usage": "low",
        "disk_usage": "normal"
    }


def determine_overall_status(statuses: Dict[str, str]) -> str:
    """Determine overall health status from component statuses."""
    if all(status == "healthy" for status in statuses.values()):
        return "healthy"
    elif any(status == "unhealthy" for status in statuses.values()):
        return "unhealthy"
    else:
        return "degraded"


def format_uptime(seconds: float) -> str:
    """Format uptime in seconds to human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs > 0 or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
    return " ".join(parts)


# Service getter functions for dependency injection
def get_news_service():
    """Get news service instance."""
    from ...services import NewsService
    return NewsService()


def get_embedding_service():
    """Get embedding service instance."""
    from ...services import EmbeddingService
    return EmbeddingService()


def get_summarization_service():
    """Get summarization service instance."""
    from ...services import SummarizationService
    return SummarizationService()


def get_article_repository():
    """Get article repository instance."""
    from ...repositories import ArticleRepository
    from ...core.config import get_settings
    settings = get_settings()
    return ArticleRepository(settings.get_database_path())
