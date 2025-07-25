"""
Custom Exceptions for AI Tech News Assistant
===========================================

This module defines custom exception classes for better error handling
and debugging throughout the application.
"""

from typing import Any, Dict, Optional


class NewsAssistantError(Exception):
    """Base exception class for all application-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(NewsAssistantError):
    """Raised when there are configuration-related issues."""
    pass


class DatabaseError(NewsAssistantError):
    """Raised when database operations fail."""
    pass


class NotFoundError(NewsAssistantError):
    """Raised when a requested resource is not found."""
    pass


class EmbeddingError(NewsAssistantError):
    """Raised when embedding generation or operations fail."""
    pass


class LLMError(NewsAssistantError):
    """Raised when LLM operations fail."""
    pass


class NewsIngestionError(NewsAssistantError):
    """Raised when news ingestion operations fail."""
    pass


class VectorStoreError(NewsAssistantError):
    """Raised when vector store operations fail."""
    pass


class ValidationError(NewsAssistantError):
    """Raised when input validation fails."""
    pass


class ExternalServiceError(NewsAssistantError):
    """Raised when external service calls fail."""
    pass


class NotFoundError(NewsAssistantError):
    """Raised when a requested resource is not found."""
    pass
