"""
Configuration Management for AI Tech News Assistant
==================================================

This module handles all application configuration using Pydantic settings.
It supports environment variables and provides type-safe configuration.
"""

import os
from typing import List, Optional, Dict
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = Field(default="AI Tech News Assistant", env="APP_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database settings
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    sqlite_database_path: str = Field(default="./data/articles.db", env="SQLITE_DATABASE_PATH")
    
    # LLM settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Ollama settings
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    
    # Embedding settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    
    # Vector database settings
    chroma_persist_directory: str = Field(
        default="./data/chroma_db", 
        env="CHROMA_PERSIST_DIRECTORY"
    )
    
    # News sources settings
    rss_sources: List[Dict[str, str]] = Field(
        default=[
            {
                "name": "O'Reilly Radar",
                "url": "https://feeds.feedburner.com/oreilly/radar",
                "description": "O'Reilly Radar tech insights"
            },
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "description": "TechCrunch startup and tech news"
            },
            {
                "name": "Ars Technica", 
                "url": "https://feeds.arstechnica.com/arstechnica/index",
                "description": "Ars Technica technology news and analysis"
            },
            {
                "name": "The Verge",
                "url": "https://www.theverge.com/rss/index.xml", 
                "description": "The Verge technology, science, art, and culture"
            },
            {
                "name": "MIT Technology Review",
                "url": "https://www.technologyreview.com/feed/",
                "description": "MIT Technology Review"
            }
        ],
        env="RSS_SOURCES"
    )
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_max_size: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Error handling settings
    enable_error_middleware: bool = Field(default=True, env="ENABLE_ERROR_MIDDLEWARE")
    enable_correlation_id: bool = Field(default=True, env="ENABLE_CORRELATION_ID")
    error_detail_in_response: bool = Field(default=False, env="ERROR_DETAIL_IN_RESPONSE")  # Only for dev
    
    # Retry and resilience settings
    default_retry_attempts: int = Field(default=3, env="DEFAULT_RETRY_ATTEMPTS")
    default_retry_delay: float = Field(default=1.0, env="DEFAULT_RETRY_DELAY")
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_endpoint: str = Field(default="/metrics", env="METRICS_ENDPOINT")
    health_check_timeout: float = Field(default=5.0, env="HEALTH_CHECK_TIMEOUT")
    
    # Rate limiting settings
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # External service timeouts
    llm_request_timeout: float = Field(default=30.0, env="LLM_REQUEST_TIMEOUT")
    embedding_request_timeout: float = Field(default=15.0, env="EMBEDDING_REQUEST_TIMEOUT")
    news_fetch_timeout: float = Field(default=10.0, env="NEWS_FETCH_TIMEOUT")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
