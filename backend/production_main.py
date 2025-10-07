"""
Production AI Tech News Assistant
===============================
Professional-grade news scraping and AI analysis platform
"""
import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings, LoggingConfig
from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.api.preferences import router as preferences_router
from app.services.database import db_service
from app.services.scraping import scraping_manager

# Setup logging
LoggingConfig.setup_logging(settings)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize database
    try:
        # Database is already initialized in db_service
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Optional: Fetch initial news on startup
    if not settings.DEBUG:
        logger.info("Triggering initial news fetch...")
        try:
            result = await scraping_manager.fetch_all_news()
            logger.info(f"Initial fetch result: {result['articles_added']} articles")
        except Exception as e:
            logger.warning(f"Initial news fetch failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api/v1" if not settings.DEBUG else "")
app.include_router(auth_router, prefix="/api/v1" if not settings.DEBUG else "")
app.include_router(preferences_router, prefix="/api/v1" if not settings.DEBUG else "")

# Health check at root level
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"status": "ok", "timestamp": "2025-09-27"}


if __name__ == "__main__":
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"📡 Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📖 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🏥 Health: http://{settings.HOST}:{settings.PORT}/health")
    logger.info(f"📰 Sources: Hacker News, Reddit Programming, GitHub Trending")
    logger.info(f"🔄 Auto-refresh: {settings.CACHE_EXPIRY_HOURS} hours")
    logger.info(f"🌐 CORS Origins: {settings.ALLOWED_ORIGINS}")
    
    uvicorn.run(
        "production_main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )