"""
AI Tech News Assistant - FastAPI Backend
========================================

Main entry point for the FastAPI application that serves the AI Tech News Assistant.
This application provides endpoints for news ingestion, summarization, and retrieval.

Author: ductringuyen0186
Repository: https://github.com/ductringuyen0186/ai-tech-news-assistant
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

import sys
from pathlib import Path

# Debug: Print Python path and CWD
_debug_cwd = Path.cwd()
_debug_backend = Path(__file__).parent

print(f"\n[DEBUG INFO]")
print(f"  CWD: {_debug_cwd}")
print(f"  Backend dir: {_debug_backend}")
print(f"  src exists: {(_debug_backend / 'src').exists()}")
print(f"  Python path[0:3]: {sys.path[0:3]}")

try:
    from src.api import api_router, root_router
    print(f"[OK] Successfully imported api_router and root_router")
    ROUTERS_LOADED = True
except Exception as e:
    print(f"[ERROR] CRITICAL: Failed to import routers from src.api: {e}")
    print(f"[INFO] Fallback API endpoints will be used")
    import traceback
    traceback.print_exc()
    ROUTERS_LOADED = False
    api_router = None
    root_router = None
    api_router = None
    root_router = None

from utils.config import get_settings
from utils.logger import get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger(__name__)

# Get application settings
try:
    settings = get_settings()
except Exception as e:
    print(f"ERROR: Failed to load settings: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="AI Tech News Assistant API",
    description="A job-market-aligned AI Tech-News Assistant that aggregates, analyzes, and presents technology news with AI-powered insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration - allow all common development and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:8001",
        "https://ai-tech-news-assistant.vercel.app",
        "https://ai-tech-news-assistant-8xbp128f1-ductringuyen0186s-projects.vercel.app",
        "https://frontend-khmjrrjtq-ductringuyen0186s-projects.vercel.app",  # Current production deployment
        "https://*.vercel.app",  # Wildcard for Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and run migrations on application startup."""
    # Disabled for now - articles table already exists in production
    # Database init causes errors with embeddings table foreign key mismatch
    logger.info("⏭️ Skipping database initialization - using existing schema")
    pass


@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    """Root endpoint providing basic API information."""
    return {
        "service": "AI Tech News Assistant API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/ping", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring and load balancers."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check including system information."""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "version": "1.0.0",
            "services": {
                "api": "healthy",
                "database": "pending",  # Will be implemented with actual DB
                "llm": "pending",       # Will be implemented with LLM service
                "vectorstore": "pending"  # Will be implemented with Chroma
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Direct PostgreSQL API endpoint using psycopg3 (Python 3.13 compatible)
@app.get("/api/news", tags=["News"])
async def get_articles_fallback(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Get articles directly from PostgreSQL database using psycopg3."""
    try:
        import os
        import psycopg
        from psycopg.rows import dict_row
        
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
        # Handle both postgres:// and postgresql:// schemes
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        offset = (page - 1) * page_size
        
        # psycopg3 uses context managers and connection strings directly
        with psycopg.connect(database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cursor:
                # Get articles
                cursor.execute("""
                    SELECT id, title, content, url, source, author, published_date, created_at
                    FROM articles
                    ORDER BY published_date DESC
                    LIMIT %s OFFSET %s
                """, (page_size, offset))
                
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    articles.append({
                        "id": row['id'],
                        "title": row['title'],
                        "content": row['content'],
                        "url": row['url'],
                        "source": row['source'],
                        "author": row['author'],
                        "published_date": row['published_date'].isoformat() if row['published_date'] else None,
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                # Get total count
                cursor.execute("SELECT COUNT(*) as count FROM articles")
                total = cursor.fetchone()['count']
        
        return {
            "items": articles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Include API routes
if api_router is not None:
    try:
        app.include_router(api_router)  # api_router already has /api prefix
    except Exception as e:
        logger.error(f"Failed to include API routes: {e}")
else:
    logger.error("API router is None - routes will not be available")

# Include root/health routes
if root_router is not None:
    try:
        app.include_router(root_router)
    except Exception as e:
        logger.error(f"Failed to include root routes: {e}")
else:
    logger.error("Root router is None - health routes will not be available")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
