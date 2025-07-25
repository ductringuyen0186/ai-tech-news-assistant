"""
News Service
==========

Business logic for news ingestion, processing, and management.
Handles RSS feed processing, article extraction, and news data operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup

from ..core.config import get_settings

settings = get_settings()
from ..core.exceptions import NewsIngestionError, ValidationError
from ..models.article import (
    Article,
    ArticleCreate,
    ArticleUpdate,
    ArticleSearchRequest,
    ArticleStats
)

logger = logging.getLogger(__name__)


class NewsService:
    """
    Service for handling news ingestion and processing operations.
    
    This service manages RSS feed processing, article extraction,
    content cleaning, and news data management with proper error
    handling and rate limiting.
    """
    
    def __init__(self):
        """Initialize the news service."""
        self.client = None
        self.rss_feeds = settings.rss_sources or []
        self.request_timeout = 30.0
        self.max_retries = 3
        
    async def initialize(self) -> None:
        """Initialize HTTP client and resources."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.request_timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
            logger.info("News service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("News service cleaned up")
    
    async def fetch_rss_feeds(self, feed_urls: Optional[List[str]] = None) -> List[ArticleCreate]:
        """
        Fetch and parse articles from RSS feeds.
        
        Args:
            feed_urls: Optional list of feed URLs. If None, uses configured feeds.
            
        Returns:
            List of parsed articles
            
        Raises:
            NewsIngestionError: If feed fetching fails
        """
        if not self.client:
            await self.initialize()
        
        feeds_to_process = feed_urls or self.rss_feeds
        if not feeds_to_process:
            raise NewsIngestionError("No RSS feeds configured")
        
        logger.info(f"Fetching {len(feeds_to_process)} RSS feeds")
        
        # Process feeds concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        tasks = [
            self._fetch_single_feed(url, semaphore) 
            for url in feeds_to_process
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results and log errors
        all_articles = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch feed {feeds_to_process[i]}: {result}")
            else:
                all_articles.extend(result)
        
        logger.info(f"Successfully fetched {len(all_articles)} articles from RSS feeds")
        return all_articles
    
    async def _fetch_single_feed(
        self, 
        feed_url: str, 
        semaphore: asyncio.Semaphore
    ) -> List[ArticleCreate]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            semaphore: Semaphore for rate limiting
            
        Returns:
            List of parsed articles from the feed
        """
        async with semaphore:
            try:
                logger.debug(f"Fetching RSS feed: {feed_url}")
                
                response = await self.client.get(feed_url)
                response.raise_for_status()
                
                return await self._parse_rss_content(response.text, feed_url)
                
            except httpx.TimeoutException:
                logger.error(f"Timeout fetching RSS feed: {feed_url}")
                return []
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching RSS feed {feed_url}: {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching RSS feed {feed_url}: {e}")
                return []
    
    async def _parse_rss_content(self, xml_content: str, source_url: str) -> List[ArticleCreate]:
        """
        Parse RSS XML content and extract articles.
        
        Args:
            xml_content: Raw XML content from RSS feed
            source_url: URL of the RSS feed source
            
        Returns:
            List of parsed articles
        """
        try:
            root = ET.fromstring(xml_content)
            articles = []
            
            # Handle both RSS and Atom feeds
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items:
                try:
                    article = await self._parse_rss_item(item, source_url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse RSS item: {e}")
                    continue
            
            logger.debug(f"Parsed {len(articles)} articles from {source_url}")
            return articles
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS XML from {source_url}: {e}")
            return []
    
    async def _parse_rss_item(self, item: ET.Element, source_url: str) -> Optional[ArticleCreate]:
        """
        Parse a single RSS item into an Article.
        
        Args:
            item: XML element representing RSS item
            source_url: URL of the RSS feed source
            
        Returns:
            Parsed article or None if parsing fails
        """
        try:
            # Extract basic fields (handle both RSS and Atom)
            title = self._get_element_text(item, ['title', '{http://www.w3.org/2005/Atom}title'])
            link = self._get_element_text(item, ['link', 'guid', '{http://www.w3.org/2005/Atom}id'])
            description = self._get_element_text(item, [
                'description', 
                'summary',
                '{http://www.w3.org/2005/Atom}summary',
                '{http://www.w3.org/2005/Atom}content'
            ])
            
            # Parse publication date
            pub_date_str = self._get_element_text(item, [
                'pubDate', 
                'published',
                '{http://www.w3.org/2005/Atom}published'
            ])
            
            if not title or not link:
                return None
            
            # Clean and process content
            title = self._clean_text(title)
            description = self._clean_html(description) if description else ""
            
            # Parse publication date
            published_at = self._parse_date(pub_date_str)
            
            # Extract additional metadata
            author = self._get_element_text(item, [
                'author', 
                'dc:creator',
                '{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name'
            ])
            
            categories = self._extract_categories(item)
            
            return ArticleCreate(
                title=title,
                url=link,
                content=description,
                author=author,
                published_at=published_at,
                source=self._extract_domain(source_url),
                categories=categories,
                metadata={
                    "rss_source": source_url,
                    "content_type": "rss"
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse RSS item: {e}")
            return None
    
    def _get_element_text(self, parent: ET.Element, tag_names: List[str]) -> Optional[str]:
        """Get text from the first matching element."""
        for tag in tag_names:
            element = parent.find(tag)
            if element is not None and element.text:
                return element.text.strip()
        return None
    
    def _extract_categories(self, item: ET.Element) -> List[str]:
        """Extract categories/tags from RSS item."""
        categories = []
        
        # Look for category elements
        for cat_elem in item.findall('category'):
            if cat_elem.text:
                categories.append(cat_elem.text.strip())
        
        # Look for Atom categories
        for cat_elem in item.findall('{http://www.w3.org/2005/Atom}category'):
            term = cat_elem.get('term')
            if term:
                categories.append(term.strip())
        
        return list(set(categories))  # Remove duplicates
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        return ' '.join(text.split())
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract plain text."""
        if not html_content:
            return ""
        
        try:
            # Parse HTML and extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            return self._clean_text(text)
            
        except Exception as e:
            logger.warning(f"Failed to clean HTML: {e}")
            return self._clean_text(html_content)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string into datetime object."""
        if not date_str:
            return None
        
        # Common date formats in RSS feeds
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%a, %d %b %Y %H:%M:%S",     # RFC 2822 without timezone
            "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601 with timezone
            "%Y-%m-%dT%H:%M:%S",         # ISO 8601 without timezone
            "%Y-%m-%d %H:%M:%S",         # Simple format
            "%Y-%m-%d",                  # Date only
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Failed to parse date: {date_str}")
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
    
    async def get_news_stats(self) -> ArticleStats:
        """
        Get statistics about news articles.
        
        Returns:
            Statistics about articles in the system
        """
        # This would typically interact with the repository layer
        # For now, return placeholder stats
        return ArticleStats(
            total_articles=0,
            articles_today=0,
            articles_this_week=0,
            unique_sources=0,
            last_updated=datetime.utcnow()
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the news service.
        
        Returns:
            Dictionary with health status information
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Test connectivity with a simple request
            test_url = "https://httpbin.org/status/200"
            response = await self.client.get(test_url, timeout=5.0)
            
            return {
                "status": "healthy",
                "http_client_ready": True,
                "rss_feeds_configured": len(self.rss_feeds),
                "test_request_time": response.elapsed.total_seconds()
            }
            
        except Exception as e:
            logger.error(f"News service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "http_client_ready": self.client is not None
            }
