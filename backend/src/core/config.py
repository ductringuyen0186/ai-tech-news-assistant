"""
Configuration Management for AI Tech News Assistant
==================================================

This module handles all application configuration using Pydantic settings.
It supports environment variables, multiple environments (dev/staging/prod),
secure secrets management, and configuration validation.
"""

import os
import secrets
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator, SecretStr, AnyHttpUrl
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseType(str, Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class Settings(BaseSettings):
    """
    Application settings with environment variable support and validation.
    
    Supports multiple environments (dev/staging/prod) with appropriate defaults
    and security configurations for each environment.
    """
    
    # Application settings
    app_name: str = Field(default="AI Tech News Assistant", env="APP_NAME")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)), env="SECRET_KEY")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT", ge=1, le=65535)
    reload: bool = Field(default=True, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS", ge=1, le=8)
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )
    allow_credentials: bool = Field(default=True, env="ALLOW_CREDENTIALS")
    allowed_methods: List[str] = Field(default=["*"], env="ALLOWED_METHODS")
    allowed_headers: List[str] = Field(default=["*"], env="ALLOWED_HEADERS")
    
    # Database settings
    database_type: DatabaseType = Field(default=DatabaseType.SQLITE, env="DATABASE_TYPE")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    sqlite_database_path: str = Field(default="./data/articles.db", env="SQLITE_DATABASE_PATH")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE", ge=1, le=20)
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW", ge=0, le=50)
    database_timeout: int = Field(default=30, env="DATABASE_TIMEOUT", ge=1, le=300)
    
    # LLM Provider Configuration
    default_llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, env="DEFAULT_LLM_PROVIDER")
    
    # OpenAI settings
    openai_api_key: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS", ge=1, le=4000)
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE", ge=0.0, le=2.0)
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT", ge=1, le=300)
    
    # Anthropic settings
    anthropic_api_key: Optional[SecretStr] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-haiku-20240307", env="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(default=1000, env="ANTHROPIC_MAX_TOKENS", ge=1, le=4000)
    anthropic_temperature: float = Field(default=0.7, env="ANTHROPIC_TEMPERATURE", ge=0.0, le=1.0)
    anthropic_timeout: int = Field(default=30, env="ANTHROPIC_TIMEOUT", ge=1, le=300)
    
    # HuggingFace settings
    huggingface_api_key: Optional[SecretStr] = Field(default=None, env="HUGGINGFACE_API_KEY")
    huggingface_model: str = Field(default="microsoft/DialoGPT-medium", env="HUGGINGFACE_MODEL")
    huggingface_timeout: int = Field(default=30, env="HUGGINGFACE_TIMEOUT", ge=1, le=300)
    
    # Ollama settings
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    ollama_timeout: int = Field(default=60, env="OLLAMA_TIMEOUT", ge=1, le=300)
    ollama_keep_alive: str = Field(default="5m", env="OLLAMA_KEEP_ALIVE")
    
    # Embedding settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE", ge=1, le=128)
    embedding_dimensions: int = Field(default=384, env="EMBEDDING_DIMENSIONS", ge=1, le=4096)
    embedding_timeout: int = Field(default=30, env="EMBEDDING_TIMEOUT", ge=1, le=300)
    
    # Vector database settings
    chroma_persist_directory: str = Field(
        default="./data/chroma_db", 
        env="CHROMA_PERSIST_DIRECTORY"
    )
    vector_similarity_threshold: float = Field(default=0.7, env="VECTOR_SIMILARITY_THRESHOLD", ge=0.0, le=1.0)
    vector_max_results: int = Field(default=10, env="VECTOR_MAX_RESULTS", ge=1, le=100)
    
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
    rss_timeout: int = Field(default=10, env="RSS_TIMEOUT", ge=1, le=60)
    rss_max_articles: int = Field(default=100, env="RSS_MAX_ARTICLES", ge=1, le=1000)
    rss_update_interval: int = Field(default=3600, env="RSS_UPDATE_INTERVAL", ge=300, le=86400)  # 5 min to 24 hours
    
    # Logging settings
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
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
    
    # Security settings
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    max_content_length: int = Field(default=16 * 1024 * 1024, env="MAX_CONTENT_LENGTH")  # 16MB
    trusted_hosts: List[str] = Field(default=["*"], env="TRUSTED_HOSTS")
    
    # Cache settings
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL", ge=60, le=86400)  # 1 min to 24 hours
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE", ge=10, le=10000)
    
    # Development settings
    auto_reload: bool = Field(default=True, env="AUTO_RELOAD")
    enable_profiling: bool = Field(default=False, env="ENABLE_PROFILING")
    enable_debug_toolbar: bool = Field(default=False, env="ENABLE_DEBUG_TOOLBAR")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                raise ValueError(f"Invalid environment: {v}. Must be one of: {list(Environment)}")
        return v
    
    @field_validator("debug")
    @classmethod
    def validate_debug_for_production(cls, v, info):
        """Ensure debug is disabled in production."""
        # Note: In Pydantic v2, we need to access other fields differently
        # This validator will be called after environment is validated
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key_length(cls, v):
        """Ensure secret key is strong enough."""
        if isinstance(v, SecretStr):
            secret_value = v.get_secret_value()
        else:
            secret_value = str(v)
        
        if len(secret_value) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @field_validator("allowed_origins")
    @classmethod
    def validate_cors_origins_for_production(cls, v):
        """Ensure CORS origins are restricted in production."""
        # Note: Production validation will be handled in model validation
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url_for_production(cls, v):
        """Ensure database URL is provided for production."""
        # Note: Production validation will be handled in model validation
        return v
    
    @field_validator("ollama_host")
    @classmethod
    def validate_ollama_host(cls, v):
        """Validate Ollama host URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Ollama host must be a valid HTTP/HTTPS URL")
        return v
    
    @model_validator(mode='after')
    def validate_production_settings(self):
        """Validate production-specific settings."""
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode cannot be enabled in production environment")
            
            if "*" in self.allowed_origins:
                raise ValueError("Wildcard CORS origins not allowed in production")
            
            if self.database_type != DatabaseType.SQLITE and not self.database_url:
                raise ValueError("Database URL is required for production with non-SQLite databases")
        
        return self
    
    def get_database_path(self) -> str:
        """Get the appropriate database path based on configuration."""
        if self.database_url:
            return self.database_url
        return self.sqlite_database_path
    
    def get_llm_config(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """Get LLM configuration for specified provider."""
        provider = provider or self.default_llm_provider
        
        configs = {
            LLMProvider.OPENAI: {
                "api_key": self.openai_api_key.get_secret_value() if self.openai_api_key else None,
                "model": self.openai_model,
                "max_tokens": self.openai_max_tokens,
                "temperature": self.openai_temperature,
                "timeout": self.openai_timeout,
            },
            LLMProvider.ANTHROPIC: {
                "api_key": self.anthropic_api_key.get_secret_value() if self.anthropic_api_key else None,
                "model": self.anthropic_model,
                "max_tokens": self.anthropic_max_tokens,
                "temperature": self.anthropic_temperature,
                "timeout": self.anthropic_timeout,
            },
            LLMProvider.HUGGINGFACE: {
                "api_key": self.huggingface_api_key.get_secret_value() if self.huggingface_api_key else None,
                "model": self.huggingface_model,
                "timeout": self.huggingface_timeout,
            },
            LLMProvider.OLLAMA: {
                "host": self.ollama_host,
                "model": self.ollama_model,
                "timeout": self.ollama_timeout,
                "keep_alive": self.ollama_keep_alive,
            },
        }
        
        return configs.get(provider, {})
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        use_enum_values = True
        validate_assignment = True
        
        # Environment-specific overrides
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )



@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings()