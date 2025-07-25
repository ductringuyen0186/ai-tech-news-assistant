"""
Main FastAPI Application
=======================

Entry point for the AI Tech News Assistant API.
Uses the refactored architecture with proper separation of concerns.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from src.core.config import get_settings
from src.core.logging import setup_logging
from src.core.exceptions import (
    DatabaseError,
    NewsIngestionError, 
    LLMError,
    EmbeddingError,
    ValidationError
)
from src.api import api_router, root_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings instance
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Handles startup and shutdown tasks for the application.
    """
    # Startup
    logger.info("Starting AI Tech News Assistant API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.sqlite_database_path}")
    
    # Initialize services (if needed)
    # This is where you could initialize shared resources
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Tech News Assistant API")
    # Cleanup resources here


# Create FastAPI application
app = FastAPI(
    title="AI Tech News Assistant",
    description="AI-powered tech news aggregation, summarization, and search API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "error_type": "ValidationError",
            "message": str(exc),
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "DATABASE_ERROR",
            "error_type": "DatabaseError", 
            "message": "Database operation failed",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@app.exception_handler(NewsIngestionError)
async def news_ingestion_error_handler(request: Request, exc: NewsIngestionError):
    """Handle news service errors."""
    logger.error(f"News service error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "NEWS_SERVICE_ERROR",
            "error_type": "NewsIngestionError",
            "message": "News operation failed",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    """Handle summarization errors."""
    logger.error(f"Summarization error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "SUMMARIZATION_ERROR",
            "error_type": "LLMError",
            "message": "Summarization failed",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@app.exception_handler(EmbeddingError)
async def embedding_error_handler(request: Request, exc: EmbeddingError):
    """Handle embedding errors."""
    logger.error(f"Embedding error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "EMBEDDING_ERROR", 
            "error_type": "EmbeddingError",
            "message": "Embedding operation failed",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


# Include routers
app.include_router(root_router)  # Health and root endpoints
app.include_router(api_router)   # Main API endpoints


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    import time
    start_time = request.state.start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
    
    return response


if __name__ == "__main__":
    import uvicorn
    import time
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
