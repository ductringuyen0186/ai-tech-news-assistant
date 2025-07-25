"""
Unit Tests for News Service
===========================

Tests for news service RSS processing and article management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import asyncio
import feedparser
from io import StringIO

from src.services.news_service import NewsService
from src.models.article import Article, ArticleCreate
from src.core.exceptions import NewsIngestionError, ValidationError


class TestNewsService:
    """Test cases for NewsService."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.rss_feeds = [
            "https://example.com/feed1.xml",
            "https://example.com/feed2.xml"
        ]
        settings.max_articles_per_feed = 10
        settings.article_content_min_length = 100
        return settings
    
    @pytest.fixture
    def service(self, mock_settings):
        """Create news service with mocked settings."""
        with patch('src.services.news_service.settings', mock_settings):
            return NewsService()
    
    @pytest.mark.asyncio
    async def test_initialization(self, service):
        """Test service initialization."""
        assert service.max_articles_per_feed == 10
        assert service.article_min_length == 100
        assert len(service.rss_feeds) == 2
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_success(self, service):
        """Test successful RSS feed fetching."""
        # Mock feedparser response
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Test Article 1',
                'link': 'https://example.com/article1',
                'summary': 'Test summary 1',
                'author': 'Test Author',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT',
                'tags': [{'term': 'technology'}, {'term': 'ai'}]
            },
            {
                'title': 'Test Article 2',
                'link': 'https://example.com/article2',
                'summary': 'Test summary 2',
                'author': 'Test Author 2',
                'published': 'Tue, 02 Jan 2024 12:00:00 GMT',
                'tags': [{'term': 'programming'}]
            }
        ]
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        assert len(articles) == 2
        assert articles[0].title == 'Test Article 1'
        assert articles[0].url == 'https://example.com/article1'
        assert 'technology' in articles[0].categories
        assert 'ai' in articles[0].categories
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_with_bozo_error(self, service):
        """Test RSS feed fetching with malformed feed."""
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = Exception("Malformed XML")
        mock_feed.entries = []
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        assert len(articles) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_with_missing_fields(self, service):
        """Test RSS feed fetching with entries missing required fields."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Complete Article',
                'link': 'https://example.com/article1',
                'summary': 'Complete summary',
                'author': 'Author 1',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT'
            },
            {
                # Missing title
                'link': 'https://example.com/article2',
                'summary': 'Summary without title',
                'author': 'Author 2'
            },
            {
                'title': 'No Link Article',
                # Missing link
                'summary': 'Summary without link'
            }
        ]
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        # Should only return the complete article
        assert len(articles) == 1
        assert articles[0].title == 'Complete Article'
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_content_too_short(self, service):
        """Test filtering out articles with content too short."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Short Article',
                'link': 'https://example.com/short',
                'summary': 'Too short',  # Less than 100 characters
                'author': 'Author',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT'
            },
            {
                'title': 'Long Article',
                'link': 'https://example.com/long',
                'summary': 'This is a much longer summary that exceeds the minimum length requirement for articles and should be accepted by the system.',
                'author': 'Author',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT'
            }
        ]
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        # Should only return the long article
        assert len(articles) == 1
        assert articles[0].title == 'Long Article'
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_respects_max_articles(self, service):
        """Test that max_articles_per_feed limit is respected."""
        service.max_articles_per_feed = 2
        
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': f'Article {i}',
                'link': f'https://example.com/article{i}',
                'summary': 'This is a long enough summary that meets the minimum length requirement for testing purposes.',
                'author': f'Author {i}',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT'
            }
            for i in range(5)  # Create 5 articles
        ]
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        # Should only return 2 articles (the limit)
        assert len(articles) == 2
    
    @pytest.mark.asyncio
    async def test_fetch_single_feed_network_error(self, service):
        """Test handling of network errors during feed fetching."""
        with patch('feedparser.parse', side_effect=Exception("Network error")):
            articles = await service._fetch_single_feed("https://example.com/feed.xml")
        
        assert len(articles) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_success(self, service):
        """Test fetching from multiple RSS feeds."""
        # Mock successful feed responses
        def mock_fetch_single_feed(url):
            if "feed1" in url:
                return asyncio.coroutine(lambda: [
                    ArticleCreate(
                        title="Article from Feed 1",
                        url="https://example.com/article1",
                        content="Content from feed 1",
                        author="Author 1",
                        source="example.com"
                    )
                ])()
            else:
                return asyncio.coroutine(lambda: [
                    ArticleCreate(
                        title="Article from Feed 2",
                        url="https://example.com/article2",
                        content="Content from feed 2",
                        author="Author 2",
                        source="example.com"
                    )
                ])()
        
        with patch.object(service, '_fetch_single_feed', side_effect=mock_fetch_single_feed):
            articles = await service.fetch_rss_feeds()
        
        assert len(articles) == 2
        assert any("Feed 1" in article.title for article in articles)
        assert any("Feed 2" in article.title for article in articles)
    
    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_with_failures(self, service):
        """Test fetching RSS feeds with some feeds failing."""
        async def mock_fetch_single_feed(url):
            if "feed1" in url:
                return [
                    ArticleCreate(
                        title="Successful Article",
                        url="https://example.com/success",
                        content="Successful content",
                        author="Author",
                        source="example.com"
                    )
                ]
            else:
                # Simulate failure for second feed
                return []
        
        with patch.object(service, '_fetch_single_feed', side_effect=mock_fetch_single_feed):
            articles = await service.fetch_rss_feeds()
        
        # Should still return articles from successful feed
        assert len(articles) == 1
        assert articles[0].title == "Successful Article"
    
    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_custom_feeds(self, service):
        """Test fetching from custom RSS feed URLs."""
        custom_feeds = ["https://custom.com/feed.xml"]
        
        async def mock_fetch_single_feed(url):
            return [
                ArticleCreate(
                    title="Custom Feed Article",
                    url="https://custom.com/article",
                    content="Custom content",
                    author="Custom Author",
                    source="custom.com"
                )
            ]
        
        with patch.object(service, '_fetch_single_feed', side_effect=mock_fetch_single_feed):
            articles = await service.fetch_rss_feeds(custom_feeds)
        
        assert len(articles) == 1
        assert articles[0].title == "Custom Feed Article"
    
    @pytest.mark.asyncio
    async def test_parse_published_date_valid_formats(self, service):
        """Test parsing of various valid date formats."""
        valid_dates = [
            "Mon, 01 Jan 2024 12:00:00 GMT",
            "2024-01-01T12:00:00Z",
            "2024-01-01 12:00:00",
            "Mon, 01 Jan 2024 12:00:00 +0000"
        ]
        
        for date_str in valid_dates:
            parsed_date = service._parse_published_date(date_str)
            assert isinstance(parsed_date, datetime)
            assert parsed_date.year == 2024
            assert parsed_date.month == 1
            assert parsed_date.day == 1
    
    @pytest.mark.asyncio
    async def test_parse_published_date_invalid_formats(self, service):
        """Test parsing of invalid date formats returns current time."""
        invalid_dates = [
            "invalid date",
            "",
            None,
            "not a date at all"
        ]
        
        for date_str in invalid_dates:
            parsed_date = service._parse_published_date(date_str)
            assert isinstance(parsed_date, datetime)
            # Should return current time (within last minute)
            time_diff = abs((datetime.now(timezone.utc) - parsed_date).total_seconds())
            assert time_diff < 60
    
    @pytest.mark.asyncio
    async def test_extract_source_from_url(self, service):
        """Test extracting source domain from URLs."""
        test_cases = [
            ("https://techcrunch.com/2024/01/01/article", "techcrunch.com"),
            ("http://example.org/path/to/article", "example.org"),
            ("https://subdomain.example.com/article", "subdomain.example.com"),
            ("invalid-url", "unknown")
        ]
        
        for url, expected_source in test_cases:
            source = service._extract_source_from_url(url)
            assert source == expected_source
    
    @pytest.mark.asyncio
    async def test_clean_content(self, service):
        """Test content cleaning functionality."""
        test_content = """
        <p>This is <strong>HTML</strong> content with <a href="link">links</a>.</p>
        <script>alert('malicious');</script>
        <div>Multiple     spaces    and\n\nnewlines</div>
        """
        
        cleaned = service._clean_content(test_content)
        
        assert "<script>" not in cleaned
        assert "<p>" not in cleaned
        assert "HTML" in cleaned
        assert "links" in cleaned
        # Should normalize whitespace
        assert "Multiple     spaces" not in cleaned
        assert "Multiple spaces" in cleaned
    
    @pytest.mark.asyncio
    async def test_get_news_stats_no_repository(self, service):
        """Test getting news stats without article repository."""
        stats = await service.get_news_stats()
        
        expected_stats = {
            "configured_feeds": len(service.rss_feeds),
            "max_articles_per_feed": service.max_articles_per_feed,
            "article_min_length": service.article_min_length,
            "total_articles": 0,
            "articles_with_summaries": 0,
            "articles_with_embeddings": 0
        }
        
        assert stats == expected_stats
    
    @pytest.mark.asyncio
    async def test_get_news_stats_with_repository(self, service):
        """Test getting news stats with article repository."""
        mock_repo = AsyncMock()
        mock_repo.get_stats.return_value = {
            "total_articles": 100,
            "articles_with_summaries": 75,
            "articles_with_embeddings": 50
        }
        
        stats = await service.get_news_stats(mock_repo)
        
        assert stats["configured_feeds"] == len(service.rss_feeds)
        assert stats["total_articles"] == 100
        assert stats["articles_with_summaries"] == 75
        assert stats["articles_with_embeddings"] == 50
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test health check with successful feed access."""
        with patch('feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.status = 200
            mock_parse.return_value = mock_feed
            
            health = await service.health_check()
        
        assert health["status"] == "healthy"
        assert health["feeds_accessible"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check_with_feed_failures(self, service):
        """Test health check with some feed failures."""
        call_count = 0
        
        def mock_parse(url):
            nonlocal call_count
            call_count += 1
            
            mock_feed = MagicMock()
            if call_count == 1:
                # First feed fails
                mock_feed.bozo = True
                mock_feed.status = 404
            else:
                # Second feed succeeds
                mock_feed.bozo = False
                mock_feed.status = 200
            return mock_feed
        
        with patch('feedparser.parse', side_effect=mock_parse):
            health = await service.health_check()
        
        assert health["status"] == "degraded"
        assert health["feeds_accessible"] == 1
        assert health["feeds_total"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check_all_feeds_fail(self, service):
        """Test health check when all feeds fail."""
        with patch('feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = True
            mock_feed.status = 500
            mock_parse.return_value = mock_feed
            
            health = await service.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["feeds_accessible"] == 0


class TestNewsServiceEdgeCases:
    """Test edge cases and error conditions for NewsService."""
    
    @pytest.fixture
    def minimal_service(self):
        """Create news service with minimal configuration."""
        settings = MagicMock()
        settings.rss_feeds = []
        settings.max_articles_per_feed = 1
        settings.article_content_min_length = 0
        
        with patch('src.services.news_service.settings', settings):
            return NewsService()
    
    @pytest.mark.asyncio
    async def test_empty_rss_feeds_list(self, minimal_service):
        """Test handling of empty RSS feeds list."""
        articles = await minimal_service.fetch_rss_feeds()
        assert len(articles) == 0
    
    @pytest.mark.asyncio
    async def test_fetch_with_zero_max_articles(self, minimal_service):
        """Test fetching with max_articles_per_feed set to 0."""
        minimal_service.max_articles_per_feed = 0
        
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Test Article',
                'link': 'https://example.com/article',
                'summary': 'Test summary',
                'author': 'Author',
                'published': 'Mon, 01 Jan 2024 12:00:00 GMT'
            }
        ]
        
        with patch('feedparser.parse', return_value=mock_feed):
            articles = await minimal_service._fetch_single_feed("https://example.com/feed.xml")
        
        assert len(articles) == 0
