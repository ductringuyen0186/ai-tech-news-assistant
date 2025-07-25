"""
Configuration Management for AI Tech News Assistant
==================================================

This module handles all application configuration using Pydantic settings.
It supports environment variables and provides type-safe configuration.
"""

import os
from typing import List, Optional, Dict
from functools import lru_cache

from pydantic import BaseSettings, Field


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
    
    # Database settings (for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # LLM settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Ollama settings
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    
    # Claude settings (using proper attribute names)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    
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
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
