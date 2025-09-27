"""
Production Configuration
=======================
"""
import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
import logging


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Info
    APP_NAME: str = "AI Tech News Assistant"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Production-grade tech news aggregation with AI insights"
    APP_MODE: str = "production"
    USE_MOCK_DATA: bool = False
    
    # Server Config
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False
    RELOAD: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./news_production.db"
    DATABASE_ECHO: bool = False
    
    # News Sources Config
    MAX_ARTICLES_PER_SOURCE: int = 15
    FETCH_TIMEOUT: int = 30
    REQUEST_DELAY: float = 1.0  # Seconds between requests
    USER_AGENT: str = "AI-News-Assistant/2.0 (+https://github.com/your-repo)"
    
    # Scraping Configuration
    SCRAPING_RATE_LIMIT: float = 2.0
    SCRAPING_MAX_RETRIES: int = 3
    SCRAPING_TIMEOUT: int = 30
    
    # Cache Settings
    CACHE_EXPIRY_HOURS: int = 2
    MAX_CACHED_ARTICLES: int = 100
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # AI/ML Configuration (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra variables in .env
    OLLAMA_MODEL: str = "llama3.2:1b"
    
    # News Sources
    HACKER_NEWS_API_BASE: str = "https://hacker-news.firebaseio.com/v0"
    REDDIT_API_BASE: str = "https://www.reddit.com/r"
    GITHUB_TRENDING_URL: str = "https://github.com/trending"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("ALLOWED_ORIGINS must be a string or list")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class LoggingConfig:
    """Logging configuration"""
    
    @staticmethod
    def setup_logging(settings: Settings):
        """Setup application logging"""
        log_level = getattr(logging, settings.LOG_LEVEL.upper())
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler if specified
        if settings.LOG_FILE:
            file_handler = logging.FileHandler(settings.LOG_FILE)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Set specific loggers
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


# Global settings instance
settings = Settings()