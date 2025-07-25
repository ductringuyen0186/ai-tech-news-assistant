"""
RSS Feed Ingestion Module for AI Tech News Assistant
===================================================

This module handles fetching and parsing RSS feeds from various tech news sources.
It extracts article metadata and stores it for further processing.

Supported sources:
- Hacker News
- TechCrunch  
- The Verge
- Ars Technica
- O'Reilly Radar
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import feedparser
import httpx
from pydantic import BaseModel, HttpUrl, Field

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Article(BaseModel):
    """Article metadata model."""
    
    id: Optional[str] = None
    title: str
    url: HttpUrl
    description: Optional[str] = None
    published_date: Optional[datetime] = None
    source: str
    source_url: str
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    content: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            HttpUrl: str
        }


class RSSFeedIngester:
    """RSS feed ingestion and processing."""
    
    DEFAULT_SOURCES = [
        {
            "name": "Hacker News",
            "url": "https://feeds.feedburner.com/oreilly/radar",
            "description": "O'Reilly Radar tech news"
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
    ]
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize RSS feed ingester.
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize SQLite database
        self.db_path = self.data_dir / "articles.db"
        self._init_database()
        
        # HTTP client for fetching feeds
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "AI Tech News Assistant/1.0 (https://github.com/ductringuyen0186/ai-tech-news-assistant)"
            }
        )
    
    def _init_database(self) -> None:
        """Initialize SQLite database for article storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    description TEXT,
                    published_date TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    author TEXT,
                    tags TEXT,
                    content TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON articles(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)")
            
            conn.commit()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    async def fetch_feed(self, feed_url: str, source_name: str) -> List[Article]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            source_name: Name of the news source
            
        Returns:
            List of parsed articles
        """
        try:
            logger.info(f"Fetching RSS feed from {source_name}: {feed_url}")
            
            # Fetch feed content
            response = await self.client.get(feed_url)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries:
                try:
                    article = self._parse_feed_entry(entry, source_name, feed_url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error parsing entry from {source_name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(articles)} articles from {source_name}")
            return articles
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching feed from {source_name}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching feed from {source_name}: {str(e)}")
            return []
    
    def _parse_feed_entry(self, entry: Any, source_name: str, source_url: str) -> Optional[Article]:
        """
        Parse a single RSS feed entry into an Article.
        
        Args:
            entry: Feedparser entry object
            source_name: Name of the news source
            source_url: URL of the RSS feed
            
        Returns:
            Parsed Article or None if parsing fails
        """
        try:
            # Extract basic information
            title = entry.get('title', '').strip()
            url = entry.get('link', '').strip()
            
            if not title or not url:
                return None
            
            # Parse published date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6])
            
            # Extract description/summary
            description = entry.get('summary', '').strip()
            if not description:
                description = entry.get('description', '').strip()
            
            # Extract author
            author = entry.get('author', '').strip()
            if not author and hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0].get('name', '').strip()
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags') and entry.tags:
                tags = [tag.get('term', '').strip() for tag in entry.tags if tag.get('term')]
            
            # Generate article ID from URL
            article_id = self._generate_article_id(url)
            
            return Article(
                id=article_id,
                title=title,
                url=url,
                description=description,
                published_date=published_date,
                source=source_name,
                source_url=source_url,
                author=author,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error parsing feed entry: {str(e)}")
            return None
    
    def _generate_article_id(self, url: str) -> str:
        """
        Generate a unique article ID from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Unique article ID
        """
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()
    
    async def ingest_all_feeds(self) -> Dict[str, Any]:
        """
        Ingest articles from all configured RSS feeds.
        
        Returns:
            Ingestion summary statistics
        """
        logger.info("Starting RSS feed ingestion for all sources")
        
        # Use configured sources or defaults
        sources = getattr(settings, 'rss_sources', None) or self.DEFAULT_SOURCES
        
        all_articles = []
        source_stats = {}
        
        # Fetch all feeds concurrently
        tasks = []
        for source in sources:
            if isinstance(source, dict):
                name = source.get('name', 'Unknown')
                url = source.get('url')
            else:
                # Handle simple string URLs
                url = source
                name = urlparse(url).netloc
            
            if url:
                tasks.append(self.fetch_feed(url, name))
        
        # Wait for all feeds to complete
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(feed_results):
            source_name = sources[i].get('name') if isinstance(sources[i], dict) else f"Source {i}"
            
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {source_name}: {str(result)}")
                source_stats[source_name] = {"articles": 0, "error": str(result)}
            else:
                articles = result
                all_articles.extend(articles)
                source_stats[source_name] = {"articles": len(articles), "error": None}
        
        # Store articles in database
        stored_count = await self.store_articles(all_articles)
        
        summary = {
            "total_fetched": len(all_articles),
            "total_stored": stored_count,
            "sources": source_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"RSS ingestion completed: {summary}")
        return summary
    
    async def store_articles(self, articles: List[Article]) -> int:
        """
        Store articles in SQLite database.
        
        Args:
            articles: List of articles to store
            
        Returns:
            Number of articles successfully stored
        """
        if not articles:
            return 0
        
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for article in articles:
                try:
                    # Convert article to dict for storage
                    article_data = article.dict()
                    
                    # Handle datetime serialization
                    if article_data['published_date']:
                        article_data['published_date'] = article_data['published_date'].isoformat()
                    
                    # Convert tags list to JSON string
                    article_data['tags'] = json.dumps(article_data['tags'])
                    
                    # Insert or update article
                    conn.execute("""
                        INSERT OR REPLACE INTO articles 
                        (id, title, url, description, published_date, source, source_url, 
                         author, tags, content, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        article_data['id'],
                        article_data['title'],
                        str(article_data['url']),
                        article_data['description'],
                        article_data['published_date'],
                        article_data['source'],
                        article_data['source_url'],
                        article_data['author'],
                        article_data['tags'],
                        article_data['content']
                    ))
                    
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Error storing article {article.title}: {str(e)}")
                    continue
            
            conn.commit()
        
        logger.info(f"Stored {stored_count} articles in database")
        return stored_count
    
    def get_articles(self, limit: int = 100, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve articles from database.
        
        Args:
            limit: Maximum number of articles to return
            source: Optional source filter
            
        Returns:
            List of article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if source:
                cursor = conn.execute("""
                    SELECT * FROM articles 
                    WHERE source = ? 
                    ORDER BY published_date DESC, created_at DESC 
                    LIMIT ?
                """, (source, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM articles 
                    ORDER BY published_date DESC, created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                article_dict = dict(row)
                # Parse tags JSON
                if article_dict['tags']:
                    article_dict['tags'] = json.loads(article_dict['tags'])
                else:
                    article_dict['tags'] = []
                articles.append(article_dict)
            
            return articles
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Convenience function for quick ingestion
async def ingest_tech_news() -> Dict[str, Any]:
    """
    Convenience function to ingest tech news from all configured sources.
    
    Returns:
        Ingestion summary
    """
    async with RSSFeedIngester() as ingester:
        return await ingester.ingest_all_feeds()
