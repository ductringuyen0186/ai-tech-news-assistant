"""
Core Configuration and Exception Tests
====================================

Tests for core configuration and exception handling to boost coverage.
"""

import pytest
from src.core.config import get_settings
from src.core.exceptions import (
    NewsAssistantError,
    ConfigurationError,
    DatabaseError,
    NotFoundError,
    EmbeddingError,
    LLMError,
    NewsIngestionError,
    VectorStoreError,
    ValidationError
)


class TestCoreConfig:
    """Test core configuration functionality."""
    
    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.app_name == "AI Tech News Assistant"
        assert settings.environment in ["development", "production", "testing"]
        assert isinstance(settings.port, int)
        assert isinstance(settings.debug, bool)
        
    def test_settings_singleton(self):
        """Test that settings is a singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestCoreExceptions:
    """Test core exception classes."""
    
    def test_base_exception(self):
        """Test base NewsAssistantError."""
        error = NewsAssistantError("Test error", error_code="TEST001")
        assert str(error) == "Test error"
        assert error.error_code == "TEST001"
        assert error.details is None
        
    def test_base_exception_with_details(self):
        """Test base exception with details."""
        details = {"key": "value"}
        error = NewsAssistantError("Test error", details=details)
        assert error.details == details
        
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Config missing")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Config missing"
        
    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Database connection failed"
        
    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Resource not found"
        
    def test_embedding_error(self):
        """Test EmbeddingError."""
        error = EmbeddingError("Embedding generation failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Embedding generation failed"
        
    def test_llm_error(self):
        """Test LLMError."""
        error = LLMError("LLM API failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "LLM API failed"
        
    def test_news_ingestion_error(self):
        """Test NewsIngestionError."""
        error = NewsIngestionError("RSS feed failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "RSS feed failed"
        
    def test_vector_store_error(self):
        """Test VectorStoreError."""
        error = VectorStoreError("Vector store operation failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Vector store operation failed"
        
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, NewsAssistantError)
        assert str(error) == "Validation failed"
        
    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from base."""
        exceptions = [
            ConfigurationError,
            DatabaseError,
            NotFoundError,
            EmbeddingError,
            LLMError,
            NewsIngestionError,
            VectorStoreError,
            ValidationError
        ]
        
        for exc_class in exceptions:
            instance = exc_class("test")
            assert isinstance(instance, NewsAssistantError)
            assert isinstance(instance, Exception)
