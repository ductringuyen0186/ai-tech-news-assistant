"""
Comprehensive Unit Tests for News Service
========================================

Tests for news service business logic operations.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, Mock
import xml.etree.ElementTree as ET

import httpx

from src.services.news_service import NewsService
from src.models.article import ArticleCreate, ArticleStats


class TestNewsService:
    """Test cases for NewsService."""
    
    @pytest.fixture
    def news_service(self):
        """Create news service instance."""
        return NewsService()
    
    @pytest.fixture
    def sample_rss_xml(self):
        """Sample RSS XML content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Tech News</title>
                <link>https://technews.com</link>
                <description>Latest tech news</description>
                <item>
                    <title>AI Revolution in 2024</title>
                    <link>https://technews.com/ai-revolution</link>
                    <description>The future of AI technology</description>
                    <pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate>
                    <author>John Doe</author>
                    <category>Technology</category>
                    <category>AI</category>
                </item>
                <item>
                    <title>Machine Learning Breakthrough</title>
                    <link>https://technews.com/ml-breakthrough</link>
                    <description>New ML algorithms discovered</description>
                    <pubDate>Sun, 31 Dec 2023 15:30:00 GMT</pubDate>
                    <author>Jane Smith</author>
                    <category>Machine Learning</category>
                </item>
            </channel>
        </rss>"""
    
    @pytest.fixture
    def sample_stats_data(self):
        """Sample article statistics data."""
        return {
            "total_articles": 100,
            "articles_with_summaries": 75,
            "articles_with_embeddings": 50,
            "top_sources": [
                {"source": "technews.com", "count": 25},
                {"source": "aiupdate.com", "count": 20}
            ],
            "recent_articles": 15
        }

    @pytest.mark.asyncio
    async def test_initialize_service(self, news_service):
        """Test service initialization."""
        await news_service.initialize()
        
        assert news_service.client is not None
        assert isinstance(news_service.client, httpx.AsyncClient)
        assert news_service.rss_feeds is not None
        assert news_service.request_timeout == 30.0
        assert news_service.max_retries == 3

    @pytest.mark.asyncio
    async def test_cleanup_service(self, news_service):
        """Test service cleanup."""
        await news_service.initialize()
        
        # Ensure client exists before cleanup
        assert news_service.client is not None
        
        await news_service.cleanup()
        
        # Client should be cleaned up
        assert news_service.client is None

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_success(self, news_service, sample_rss_xml):
        """Test successful RSS feed fetching."""
        mock_response = Mock()
        mock_response.text = sample_rss_xml
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)
            
            feed_urls = ["https://technews.com/rss"]
            articles = await news_service.fetch_rss_feeds(feed_urls)
            
            assert len(articles) == 2
            assert articles[0].title == "AI Revolution in 2024"
            assert articles[0].url == "https://technews.com/ai-revolution"
            assert articles[0].author == "John Doe"
            assert "Technology" in articles[0].categories
            assert "AI" in articles[0].categories
            
            assert articles[1].title == "Machine Learning Breakthrough"
            assert articles[1].url == "https://technews.com/ml-breakthrough"
            assert articles[1].author == "Jane Smith"

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_http_error(self, news_service):
        """Test RSS feed fetching with HTTP error."""
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=Mock()
            ))
            
            feed_urls = ["https://invalid.com/rss"]
            articles = await news_service.fetch_rss_feeds(feed_urls)
            
            # Should return empty list on error
            assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_network_error(self, news_service):
        """Test RSS feed fetching with network error."""
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            
            feed_urls = ["https://unreachable.com/rss"]
            articles = await news_service.fetch_rss_feeds(feed_urls)
            
            # Should return empty list on error
            assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_single_feed_success(self, news_service, sample_rss_xml):
        """Test fetching a single RSS feed."""
        mock_response = Mock()
        mock_response.text = sample_rss_xml
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)
            
            articles = await news_service._fetch_single_feed("https://technews.com/rss")
            
            assert len(articles) == 2
            assert all(isinstance(article, ArticleCreate) for article in articles)

    @pytest.mark.asyncio
    async def test_fetch_single_feed_with_retries(self, news_service):
        """Test single feed fetching with retries."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.text = "<?xml version='1.0'?><rss><channel></channel></rss>"
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(side_effect=[
                httpx.ConnectError("Connection failed"),
                httpx.TimeoutException("Timeout"),
                mock_response
            ])
            
            articles = await news_service._fetch_single_feed("https://technews.com/rss")
            
            # Should succeed after retries
            assert isinstance(articles, list)
            assert mock_client.get.call_count == 3

    def test_parse_rss_content(self, news_service, sample_rss_xml):
        """Test RSS content parsing."""
        articles = asyncio.run(news_service._parse_rss_content(sample_rss_xml, "https://technews.com"))
        
        assert len(articles) == 2
        assert articles[0].title == "AI Revolution in 2024"
        assert articles[0].source == "technews.com"
        assert articles[1].title == "Machine Learning Breakthrough"

    def test_parse_rss_content_invalid_xml(self, news_service):
        """Test parsing invalid RSS content."""
        invalid_xml = "This is not valid XML content"
        
        articles = asyncio.run(news_service._parse_rss_content(invalid_xml, "https://test.com"))
        
        # Should return empty list for invalid XML
        assert articles == []

    def test_parse_rss_item_complete(self, news_service):
        """Test parsing complete RSS item."""
        xml_content = """
        <item>
            <title>Test Article</title>
            <link>https://test.com/article</link>
            <description>Test description content</description>
            <pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate>
            <author>Test Author</author>
            <category>Technology</category>
            <category>AI</category>
        </item>
        """
        
        item = ET.fromstring(xml_content)
        article = asyncio.run(news_service._parse_rss_item(item, "https://test.com"))
        
        assert article is not None
        assert article.title == "Test Article"
        assert article.url == "https://test.com/article"
        assert article.content == "Test description content"
        assert article.author == "Test Author"
        assert article.source == "test.com"
        assert "Technology" in article.categories
        assert "AI" in article.categories

    def test_parse_rss_item_minimal(self, news_service):
        """Test parsing minimal RSS item."""
        xml_content = """
        <item>
            <title>Minimal Article</title>
            <link>https://test.com/minimal</link>
        </item>
        """
        
        item = ET.fromstring(xml_content)
        article = asyncio.run(news_service._parse_rss_item(item, "https://test.com"))
        
        assert article is not None
        assert article.title == "Minimal Article"
        assert article.url == "https://test.com/minimal"
        assert article.content == ""
        assert article.author is None
        assert article.categories == []

    def test_parse_rss_item_missing_required(self, news_service):
        """Test parsing RSS item missing required fields."""
        xml_content = """
        <item>
            <description>Article without title or link</description>
        </item>
        """
        
        item = ET.fromstring(xml_content)
        article = asyncio.run(news_service._parse_rss_item(item, "https://test.com"))
        
        # Should return None for items missing required fields
        assert article is None

    def test_get_element_text(self, news_service):
        """Test element text extraction."""
        xml_content = """
        <root>
            <title>Test Title</title>
            <alt_title>Alternative Title</alt_title>
            <description><![CDATA[Rich content with <b>HTML</b>]]></description>
        </root>
        """
        
        root = ET.fromstring(xml_content)
        
        # Test single tag
        title = news_service._get_element_text(root, ["title"])
        assert title == "Test Title"
        
        # Test multiple tags (should return first found)
        title_alt = news_service._get_element_text(root, ["missing", "title", "alt_title"])
        assert title_alt == "Test Title"
        
        # Test CDATA content
        description = news_service._get_element_text(root, ["description"])
        assert "Rich content with" in description
        
        # Test missing element
        missing = news_service._get_element_text(root, ["nonexistent"])
        assert missing is None

    def test_extract_categories(self, news_service):
        """Test category extraction from RSS item."""
        xml_content = """
        <item>
            <category>Technology</category>
            <category>AI</category>
            <category>Machine Learning</category>
        </item>
        """
        
        item = ET.fromstring(xml_content)
        categories = news_service._extract_categories(item)
        
        assert len(categories) == 3
        assert "Technology" in categories
        assert "AI" in categories
        assert "Machine Learning" in categories

    def test_extract_categories_empty(self, news_service):
        """Test category extraction with no categories."""
        xml_content = "<item></item>"
        
        item = ET.fromstring(xml_content)
        categories = news_service._extract_categories(item)
        
        assert categories == []

    def test_clean_text(self, news_service):
        """Test text cleaning functionality."""
        # Test HTML removal
        html_text = "This has <b>bold</b> and <i>italic</i> text"
        cleaned = news_service._clean_text(html_text)
        assert cleaned == "This has bold and italic text"
        
        # Test whitespace normalization
        spaced_text = "Too   much    whitespace\n\nhere"
        cleaned = news_service._clean_text(spaced_text)
        assert cleaned == "Too much whitespace here"
        
        # Test empty/None handling
        assert news_service._clean_text("") == ""
        assert news_service._clean_text(None) == ""

    def test_clean_html(self, news_service):
        """Test HTML content cleaning."""
        html_content = """
        <div>
            <p>This is a <strong>test</strong> paragraph.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <script>alert('malicious');</script>
        </div>
        """
        
        cleaned = news_service._clean_html(html_content)
        
        assert "This is a test paragraph." in cleaned
        assert "Item 1" in cleaned
        assert "Item 2" in cleaned
        assert "<script>" not in cleaned
        assert "alert('malicious')" not in cleaned

    def test_parse_date_formats(self, news_service):
        """Test date parsing with various formats."""
        # RFC 2822 format
        rfc_date = "Mon, 01 Jan 2024 10:00:00 GMT"
        parsed = news_service._parse_date(rfc_date)
        assert parsed is not None
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 1
        
        # ISO format
        iso_date = "2024-01-01T10:00:00Z"
        parsed = news_service._parse_date(iso_date)
        assert parsed is not None
        assert parsed.year == 2024
        
        # Invalid date
        invalid_date = "Not a date"
        parsed = news_service._parse_date(invalid_date)
        assert parsed is None
        
        # None input
        parsed = news_service._parse_date(None)
        assert parsed is None

    def test_extract_domain(self, news_service):
        """Test domain extraction from URLs."""
        # Standard URL
        domain = news_service._extract_domain("https://www.example.com/path/to/article")
        assert domain == "www.example.com"
        
        # URL with subdomain
        domain = news_service._extract_domain("https://news.technews.com/article")
        assert domain == "news.technews.com"
        
        # HTTP URL
        domain = news_service._extract_domain("http://simple.com")
        assert domain == "simple.com"
        
        # Invalid URL
        domain = news_service._extract_domain("not-a-url")
        assert domain == "not-a-url"

    @pytest.mark.asyncio
    async def test_get_news_stats(self, news_service, sample_stats_data):
        """Test news statistics retrieval."""
        # Mock the repository dependency
        with patch('src.services.news_service.ArticleRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get_stats = AsyncMock(return_value=sample_stats_data)
            
            stats = await news_service.get_news_stats()
            
            assert isinstance(stats, ArticleStats)
            assert stats.total_articles == 100
            assert stats.articles_with_summaries == 75
            assert stats.articles_with_embeddings == 50
            assert len(stats.top_sources) == 2

    @pytest.mark.asyncio
    async def test_health_check(self, news_service):
        """Test service health check."""
        await news_service.initialize()
        
        health = await news_service.health_check()
        
        assert isinstance(health, dict)
        assert health["status"] == "healthy"
        assert "rss_feeds_count" in health
        assert "client_status" in health
        assert health["client_status"] == "initialized"

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self, news_service):
        """Test health check when service is not initialized."""
        # Don't initialize the service
        health = await news_service.health_check()
        
        assert health["client_status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_default_feeds(self, news_service, sample_rss_xml):
        """Test fetching RSS feeds using default configuration."""
        mock_response = Mock()
        mock_response.text = sample_rss_xml
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        # Set up default feeds
        news_service.rss_feeds = ["https://default1.com/rss", "https://default2.com/rss"]
        
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Call without feed_urls parameter to use defaults
            articles = await news_service.fetch_rss_feeds()
            
            assert len(articles) == 4  # 2 articles × 2 feeds
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_feed_processing(self, news_service, sample_rss_xml):
        """Test concurrent processing of multiple RSS feeds."""
        mock_response = Mock()
        mock_response.text = sample_rss_xml
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        feed_urls = [f"https://feed{i}.com/rss" for i in range(5)]
        
        with patch.object(news_service, 'client') as mock_client:
            mock_client.get = AsyncMock(return_value=mock_response)
            
            start_time = datetime.now()
            articles = await news_service.fetch_rss_feeds(feed_urls)
            end_time = datetime.now()
            
            # Should process all feeds concurrently
            assert len(articles) == 10  # 2 articles × 5 feeds
            assert mock_client.get.call_count == 5
            
            # Should complete quickly due to concurrency
            processing_time = (end_time - start_time).total_seconds()
            assert processing_time < 5.0  # Should be much faster than sequential
