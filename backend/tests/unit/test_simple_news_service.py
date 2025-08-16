"""
Simple News Service Tests
========================

Basic working tests for NewsService to improve coverage.
"""

import pytest

from src.services.news_service import NewsService


class TestSimpleNewsService:
    """Simple test cases for NewsService."""
    
    @pytest.fixture
    def service(self):
        """Create a news service instance."""
        return NewsService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.client is None
        assert isinstance(service.rss_feeds, list)
        assert service.request_timeout == 30.0
        assert service.max_retries == 3
    
    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization method."""
        await service.initialize()
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_cleanup(self, service):
        """Test service cleanup method."""
        await service.initialize()
        await service.cleanup()
        # Should not raise an exception
    
    def test_clean_text(self, service):
        """Test text cleaning method."""
        html_text = "<p>Hello <strong>world</strong>!</p>"
        cleaned = service._clean_text(html_text)
        assert "Hello world!" in cleaned
        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
    
    def test_extract_domain(self, service):
        """Test domain extraction method."""
        url = "https://example.com/path/to/article"
        domain = service._extract_domain(url)
        assert domain == "example.com"
        
    def test_extract_domain_invalid(self, service):
        """Test domain extraction with invalid URL."""
        domain = service._extract_domain("invalid-url")
        assert domain == "invalid-url"
    
    @pytest.mark.asyncio
    async def test_get_news_stats(self, service):
        """Test getting news statistics."""
        stats = await service.get_news_stats()
        assert hasattr(stats, 'total_articles')
        assert hasattr(stats, 'articles_with_summaries') 
        assert isinstance(stats.total_articles, int)
    
    @pytest.mark.asyncio 
    async def test_health_check(self, service):
        """Test health check method."""
        health = await service.health_check()
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "last_checked" in health
