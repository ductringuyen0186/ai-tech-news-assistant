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

print(f"\n🔍 DEBUG INFO:")
print(f"  CWD: {_debug_cwd}")
print(f"  Backend dir: {_debug_backend}")
print(f"  src exists: {(_debug_backend / 'src').exists()}")
print(f"  Python path[0:3]: {sys.path[0:3]}")

try:
    from src.api import api_router, root_router
    print(f"✅ Successfully imported api_router and root_router")
except Exception as e:
    print(f"❌ CRITICAL: Failed to import routers from src.api: {e}")
    import traceback
    traceback.print_exc()
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


# Temporary fallback API endpoint for articles (until routes are fixed)
@app.get("/api/news", tags=["News"])
async def get_articles_fallback(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """Temporary fallback endpoint to serve articles from database."""
    try:
        import os
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        database_url = os.getenv("DATABASE_URL", "")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        offset = (page - 1) * page_size
        
        # Get articles
        result = session.execute(text("""
            SELECT id, title, content, url, source, author, published_date, created_at
            FROM articles
            ORDER BY published_date DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": page_size, "offset": offset})
        
        articles = []
        for row in result:
            articles.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "url": row[3],
                "source": row[4],
                "author": row[5],
                "published_date": row[6].isoformat() if row[6] else None,
                "created_at": row[7].isoformat() if row[7] else None
            })
        
        # Get total count
        count_result = session.execute(text("SELECT COUNT(*) FROM articles"))
        total = count_result.scalar()
        
        session.close()
        
        return {
            "items": articles,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Fallback API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
