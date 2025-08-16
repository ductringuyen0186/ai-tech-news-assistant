"""
AI Tech News Assistant
====================

A professional AI-powered news aggregation and analysis system.
Features RSS ingestion, LLM summarization, embedding generation, and semantic search.

This package contains the refactored, production-ready codebase with:
- Clean layered architecture (API -> Services -> Repositories)
- Comprehensive data models and type safety
- Professional error handling and logging
- Extensive test coverage
- Proper separation of concerns
"""

__version__ = "1.0.0"
__author__ = "AI Tech News Assistant Team"
__description__ = "AI-powered tech news aggregation and analysis"

from .core.config import get_settings
from .core.exceptions import (
    DatabaseError,
    NewsIngestionError,
    LLMError,
    EmbeddingError,
    ValidationError
)

# Create settings instance for backwards compatibility
settings = get_settings()

__all__ = [
    "settings",
    "DatabaseError",
    "NewsIngestionError", 
    "LLMError",
    "EmbeddingError",
    "ValidationError"
]
