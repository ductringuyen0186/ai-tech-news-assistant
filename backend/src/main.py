"""
Main FastAPI Application
=======================

Entry point for the AI Tech News Assistant API.
Uses the refactored architecture with proper separation of concerns,
comprehensive error handling, and monitoring.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.core.middleware import (
    ErrorHandlingMiddleware, 
    HealthCheckMiddleware,
    create_custom_error_handlers
)
from src.core.exceptions import (
    ValidationError,
    NotFoundError,
    RateLimitError
)
from src.api import api_router, root_router

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Get settings instance
settings = get_settings()

# Global health check middleware instance for metrics
health_middleware = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Handles startup and shutdown tasks for the application.
    """
    # Startup
    logger.info(
        "Starting AI Tech News Assistant API",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
            "version": app.version
        }
    )
    
    # Log important configuration
    logger.info(
        "Application configuration loaded",
        extra={
            "database_path": settings.sqlite_database_path,
            "log_level": settings.log_level,
            "cors_origins": settings.allowed_origins,
            "error_middleware_enabled": settings.enable_error_middleware,
            "metrics_enabled": settings.enable_metrics
        }
    )
    
    # Initialize services (if needed)
    # This is where you could initialize shared resources like:
    # - Database connections
    # - External service clients
    # - Cache instances
    # - Background tasks
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Tech News Assistant API")
    # Cleanup resources here


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="AI Tech News Assistant",
    description="AI-powered tech news aggregation, summarization, and search API with comprehensive error handling and monitoring",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    debug=settings.debug
)

# Add comprehensive error handling middleware
if settings.enable_error_middleware:
    app.add_middleware(ErrorHandlingMiddleware)
    logger.info("Error handling middleware enabled")

# Add health check middleware for monitoring
if settings.enable_metrics:
    health_middleware = HealthCheckMiddleware(app)
    app.add_middleware(HealthCheckMiddleware)
    logger.info("Health check middleware enabled")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"]  # Expose correlation ID to clients
)

# Add custom exception handlers for specific types
custom_handlers = create_custom_error_handlers()
for exception_type, handler in custom_handlers.items():
    app.add_exception_handler(exception_type, handler)

logger.info("Custom exception handlers registered")

# Include routers
app.include_router(root_router)  # Health and root endpoints
app.include_router(api_router)   # Main API endpoints

logger.info("API routes registered")


# Add metrics endpoint if enabled
if settings.enable_metrics and health_middleware:
    @app.get(settings.metrics_endpoint)
    async def get_metrics():
        """Get application health metrics."""
        return health_middleware.get_metrics()


# Enhanced startup event logging
@app.on_event("startup")
async def startup_event():
    """Log startup completion with timing."""
    logger.info(
        "Application startup completed",
        extra={
            "startup_time": time.time(),
            "pid": __import__("os").getpid()
        }
    )


@app.on_event("shutdown") 
async def shutdown_event():
    """Log shutdown event."""
    logger.info(
        "Application shutdown initiated",
        extra={
            "shutdown_time": time.time()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Enhanced uvicorn configuration
    uvicorn_config = {
        "app": "src.main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug and settings.environment == "development",
        "log_level": settings.log_level.lower(),
        "access_log": True,
        "server_header": False,  # Don't expose server details
        "date_header": False     # Don't add date header
    }
    
    logger.info(
        "Starting uvicorn server",
        extra={
            "host": settings.host,
            "port": settings.port,
            "reload": uvicorn_config["reload"],
            "log_level": settings.log_level
        }
    )
    
    # Run the application
    uvicorn.run(**uvicorn_config)
