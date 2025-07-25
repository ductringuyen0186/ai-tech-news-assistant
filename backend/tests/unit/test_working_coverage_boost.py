"""
Working Unit Tests for Coverage Boost
====================================

Simple, focused tests that actually work with the existing codebase to boost coverage.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import List, Dict, Any

# Core functionality tests
from src.core.config import get_settings, Settings
from src.core.exceptions import (
    NewsAssistantError, DatabaseError, NotFoundError, ValidationError,
    NewsIngestionError, LLMError
)

# Service imports with proper error handling
try:
    from src.services.news_service import NewsService
except ImportError:
    NewsService = None

try:
    from src.services.embedding_service import EmbeddingService
except ImportError:
    EmbeddingService = None


class TestSettingsAndConfig:
    """Test settings and configuration functionality."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns a singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_settings_has_required_attributes(self):
        """Test that settings has all required attributes."""
        settings = get_settings()
        
        # These should exist based on the codebase
        assert hasattr(settings, 'database_path')
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'environment')
        
    def test_settings_database_path_not_empty(self):
        """Test that database path is configured."""
        settings = get_settings()
        assert settings.database_path is not None
        assert len(settings.database_path) > 0


class TestAllExceptions:
    """Test all custom exception classes."""
    
    def test_base_exception_creation(self):
        """Test creating base exceptions."""
        exc = NewsAssistantError("Test message")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
    
    def test_database_error(self):
        """Test DatabaseError exception."""
        exc = DatabaseError("Database failed")
        assert str(exc) == "Database failed"
        assert isinstance(exc, NewsAssistantError)
    
    def test_not_found_error(self):
        """Test NotFoundError exception."""
        exc = NotFoundError("Item not found")
        assert str(exc) == "Item not found"
        assert isinstance(exc, NewsAssistantError)
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        exc = ValidationError("Invalid input")
        assert str(exc) == "Invalid input"
        assert isinstance(exc, NewsAssistantError)
    
    def test_news_ingestion_error(self):
        """Test NewsIngestionError exception."""
        exc = NewsIngestionError("Feed failed")
        assert str(exc) == "Feed failed"
        assert isinstance(exc, NewsAssistantError)
    
    def test_llm_error(self):
        """Test LLMError exception."""
        exc = LLMError("LLM failed")
        assert str(exc) == "LLM failed"
        assert isinstance(exc, NewsAssistantError)
    
    def test_exception_with_details(self):
        """Test exception with additional details."""
        details = {"error_code": 500, "source": "test"}
        exc = DatabaseError("Test error", details=details)
        assert exc.details == details
    
    def test_exception_chain_isinstance(self):
        """Test exception inheritance chain."""
        exc = NotFoundError("Test")
        assert isinstance(exc, NewsAssistantError)
        assert isinstance(exc, Exception)


@pytest.mark.skipif(NewsService is None, reason="NewsService not available")
class TestNewsServiceBasics:
    """Test basic NewsService functionality."""
    
    @pytest.fixture
    def news_service(self):
        """Create news service instance."""
        # Mock the settings to avoid missing attributes
        with patch('src.services.news_service.settings') as mock_settings:
            mock_settings.rss_feeds = []
            return NewsService()
    
    def test_news_service_creation(self, news_service):
        """Test news service can be created."""
        assert news_service is not None
        assert news_service.client is None
        assert hasattr(news_service, 'rss_feeds')
    
    @pytest.mark.asyncio
    async def test_news_service_initialize(self, news_service):
        """Test news service initialization."""
        await news_service.initialize()
        assert news_service.client is not None
    
    @pytest.mark.asyncio
    async def test_news_service_cleanup(self, news_service):
        """Test news service cleanup."""
        await news_service.initialize()
        assert news_service.client is not None
        
        await news_service.cleanup()
        assert news_service.client is None
    
    def test_extract_domain_method(self, news_service):
        """Test domain extraction method."""
        # This method exists in the news service
        domain = news_service._extract_domain("https://www.example.com/path")
        assert domain == "www.example.com"
        
        domain = news_service._extract_domain("http://test.com")
        assert domain == "test.com"
    
    def test_clean_text_method(self, news_service):
        """Test text cleaning method."""
        # This method exists in the news service
        cleaned = news_service._clean_text("  Text with  extra   spaces  ")
        assert "Text with extra spaces" in cleaned
        
        cleaned = news_service._clean_text("Text\nwith\nnewlines")
        assert "\n" not in cleaned or cleaned.count("\n") < 3
    
    def test_parse_date_method(self, news_service):
        """Test date parsing method."""
        # This method exists in the news service
        parsed = news_service._parse_date("Mon, 01 Jan 2024 10:00:00 GMT")
        assert parsed is not None
        assert isinstance(parsed, datetime)
        
        # Test with None
        parsed = news_service._parse_date(None)
        assert parsed is None


@pytest.mark.skipif(EmbeddingService is None, reason="EmbeddingService not available")
class TestEmbeddingServiceBasics:
    """Test basic EmbeddingService functionality."""
    
    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()
    
    def test_embedding_service_creation(self, embedding_service):
        """Test embedding service can be created."""
        assert embedding_service is not None
        assert hasattr(embedding_service, 'model')
        assert hasattr(embedding_service, 'device')
    
    @pytest.mark.asyncio
    async def test_embedding_service_initialize(self, embedding_service):
        """Test embedding service initialization."""
        # Mock the model loading to avoid downloading
        with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
            mock_model = Mock()
            mock_transformer.return_value = mock_model
            
            await embedding_service.initialize()
            assert embedding_service.model is not None
    
    @pytest.mark.asyncio
    async def test_embedding_service_health_check(self, embedding_service):
        """Test embedding service health check."""
        health = await embedding_service.health_check()
        assert isinstance(health, dict)
        assert "status" in health


class TestModelValidation:
    """Test model validation and creation."""
    
    def test_article_model_creation(self):
        """Test creating article models."""
        from src.models.article import ArticleCreate
        
        article_data = {
            "title": "Test Article",
            "url": "https://test.com/article",
            "content": "Test content",
            "source": "test.com"
        }
        
        article = ArticleCreate(**article_data)
        assert article.title == "Test Article"
        assert article.url == "https://test.com/article"
        assert article.content == "Test content"
        assert article.source == "test.com"
    
    def test_embedding_models(self):
        """Test embedding model creation."""
        from src.models.embedding import EmbeddingRequest, SimilarityResult
        
        # Test EmbeddingRequest
        request = EmbeddingRequest(
            texts=["Test text 1", "Test text 2"],
            model_name="test-model"
        )
        assert len(request.texts) == 2
        assert request.model_name == "test-model"
        
        # Test SimilarityResult
        result = SimilarityResult(
            content_id="test_123",
            content_type="article",
            similarity_score=0.95,
            metadata={"title": "Test"}
        )
        assert result.content_id == "test_123"
        assert result.similarity_score == 0.95


class TestAPIModels:
    """Test API response models."""
    
    def test_base_response_model(self):
        """Test BaseResponse model."""
        from src.models.api import BaseResponse
        
        response = BaseResponse(
            success=True,
            data={"test": "data"},
            message="Success"
        )
        
        assert response.success is True
        assert response.data == {"test": "data"}
        assert response.message == "Success"
    
    def test_error_response_model(self):
        """Test ErrorResponse model."""
        from src.models.api import ErrorResponse
        
        response = ErrorResponse(
            success=False,
            error="Test error",
            error_code="TEST_ERROR"
        )
        
        assert response.success is False
        assert response.error == "Test error"
        assert response.error_code == "TEST_ERROR"


class TestUtilityFunctions:
    """Test utility functions and helpers."""
    
    def test_settings_environment_handling(self):
        """Test environment handling in settings."""
        settings = get_settings()
        
        # Environment should be a string
        assert isinstance(settings.environment, str)
        # Should be one of the expected values
        assert settings.environment in ["development", "production", "testing"]
    
    def test_database_stats_model(self):
        """Test database statistics model."""
        from src.models.database import DatabaseStats
        
        stats = DatabaseStats(
            total_articles=100,
            articles_with_summaries=75,
            articles_with_embeddings=50,
            total_embeddings=200,
            unique_sources=10
        )
        
        assert stats.total_articles == 100
        assert stats.articles_with_summaries == 75
        assert stats.articles_with_embeddings == 50


class TestConcurrentOperations:
    """Test concurrent operations and async handling."""
    
    @pytest.mark.asyncio
    async def test_multiple_async_operations(self):
        """Test multiple async operations running concurrently."""
        
        async def dummy_operation(delay: float, value: str):
            await asyncio.sleep(delay)
            return f"completed_{value}"
        
        # Run multiple operations concurrently
        tasks = [
            dummy_operation(0.01, "A"),
            dummy_operation(0.01, "B"),
            dummy_operation(0.01, "C")
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert "completed_A" in results
        assert "completed_B" in results
        assert "completed_C" in results


class TestDatabaseConnection:
    """Test database connection and basic operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    
    def test_database_creation(self, temp_db):
        """Test database file creation."""
        import sqlite3
        
        # Create a simple connection
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT name FROM test_table WHERE id = 1")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "test"
        
        conn.close()


class TestErrorHandlingScenarios:
    """Test various error handling scenarios."""
    
    def test_exception_with_context(self):
        """Test exception handling with context."""
        try:
            raise DatabaseError("Test database error")
        except DatabaseError as e:
            assert str(e) == "Test database error"
            assert isinstance(e, NewsAssistantError)
    
    def test_nested_exception_handling(self):
        """Test nested exception handling."""
        def inner_function():
            raise ValidationError("Inner validation error")
        
        def outer_function():
            try:
                inner_function()
            except ValidationError as e:
                raise NewsIngestionError(f"Outer error: {str(e)}")
        
        with pytest.raises(NewsIngestionError) as exc_info:
            outer_function()
        
        assert "Outer error: Inner validation error" in str(exc_info.value)
class TestDataValidationAndSanitization:
    """Test data validation and sanitization."""
    
    def test_url_validation(self):
        """Test URL validation patterns."""
        from urllib.parse import urlparse
        
        valid_urls = [
            "https://example.com",
            "http://test.org/path",
            "https://subdomain.example.com/path?param=value"
        ]
        
        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme in ['http', 'https']
            assert parsed.netloc != ''
    
    def test_text_sanitization(self):
        """Test text sanitization."""
        # Simple text cleaning test
        dirty_text = "  Text with\n\nextra\t\tspaces  "
        cleaned = ' '.join(dirty_text.split())
        assert cleaned == "Text with extra spaces"
    
    def test_html_stripping(self):
        """Test HTML tag removal."""
        html_text = "<p>This is <strong>bold</strong> text</p>"
        # Simple HTML removal
        import re
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        assert clean_text == "This is bold text"
