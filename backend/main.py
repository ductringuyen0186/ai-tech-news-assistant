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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

from api.routes import router as api_router
from utils.config import get_settings
from utils.logger import get_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = get_logger(__name__)

# Get application settings
settings = get_settings()

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
        "https://*.vercel.app",  # Wildcard for Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


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


# Include API routes
app.include_router(api_router, prefix="/api")


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
