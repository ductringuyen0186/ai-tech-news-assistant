"""
RSS Feed Ingestion Module for AI Tech News Assistant
===================================================

This module handles fetching and parsing RSS feeds from various tech news sources.
It extracts article metadata and content for further processing.

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
from urllib.parse import urlparse

import feedparser
import httpx
from pydantic import BaseModel, HttpUrl, Field

from utils.config import get_settings
from utils.logger import get_logger
from ingestion.content_parser import ContentParser

logger = get_logger(__name__)
settings = get_settings()


class RSSFeedManager:
    """
    RSS Feed Manager for handling multiple news sources.
    
    This class provides a unified interface for fetching articles
    from various RSS feeds with proper error handling and rate limiting.
    """
    
    def __init__(self):
        """Initialize the RSS feed manager."""
        self.session = None
        self.timeout = 30.0
        self.max_articles_per_feed = 20
        
        # Default tech news sources
        self.default_sources = [
            {
                "name": "Hacker News",
                "url": "https://hnrss.org/frontpage?limit=20",
                "source_type": "rss"
            },
            {
                "name": "TechCrunch", 
                "url": "https://techcrunch.com/feed/",
                "source_type": "rss"
            },
            {
                "name": "The Verge",
                "url": "https://www.theverge.com/rss/index.xml",
                "source_type": "rss"
            }
        ]
    
    async def init_session(self):
        """Initialize HTTP session."""
        if not self.session:
            self.session = httpx.AsyncClient(timeout=self.timeout)
    
    async def fetch_articles(self, feed_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            limit: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        await self.init_session()
        
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            response = await self.session.get(feed_url)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:limit]:
                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "description": entry.get("summary", ""),
                    "published_date": self._parse_date(entry.get("published")),
                    "source": feed.feed.get("title", "Unknown"),
                    "source_url": feed_url,
                    "author": entry.get("author", ""),
                    "content": entry.get("summary", "")
                }
                articles.append(article)
            
            logger.info(f"Successfully fetched {len(articles)} articles from {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
            return []
    
    async def fetch_all_sources(self, limit_per_source: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch articles from all default sources.
        
        Args:
            limit_per_source: Maximum articles per source
            
        Returns:
            Combined list of articles from all sources
        """
        all_articles = []
        
        for source in self.default_sources:
            articles = await self.fetch_articles(source["url"], limit_per_source)
            all_articles.extend(articles)
        
        return all_articles
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            import dateutil.parser
            return dateutil.parser.parse(date_str)
        except:
            return datetime.now()
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.aclose()


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
                    content_length INTEGER,
                    content_parsed_at TEXT,
                    content_parser_method TEXT,
                    content_metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON articles(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_length ON articles(content_length)")
            
            # Add new columns if they don't exist (for existing databases)
            try:
                conn.execute("ALTER TABLE articles ADD COLUMN content_length INTEGER")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                conn.execute("ALTER TABLE articles ADD COLUMN content_parsed_at TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                conn.execute("ALTER TABLE articles ADD COLUMN content_parser_method TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                conn.execute("ALTER TABLE articles ADD COLUMN content_metadata TEXT")
            except sqlite3.OperationalError:
                pass
            
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
    
    async def ingest_all_feeds(self, parse_content: bool = False) -> Dict[str, Any]:
        """
        Ingest articles from all configured RSS feeds.
        
        Args:
            parse_content: Whether to parse full article content (slower but more complete)
        
        Returns:
            Ingestion summary statistics
        """
        logger.info(f"Starting RSS feed ingestion for all sources (parse_content={parse_content})")
        
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
        
        # Store articles in database (with optional content parsing)
        stored_count = await self.store_articles(all_articles, parse_content=parse_content)
        
        summary = {
            "total_fetched": len(all_articles),
            "total_stored": stored_count,
            "content_parsed": parse_content,
            "sources": source_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"RSS ingestion completed: {summary}")
        return summary
    
    async def store_articles(self, articles: List[Article], parse_content: bool = True) -> int:
        """
        Store articles in SQLite database with optional content parsing.
        
        Args:
            articles: List of articles to store
            parse_content: Whether to parse full article content
            
        Returns:
            Number of articles successfully stored
        """
        if not articles:
            return 0
        
        stored_count = 0
        
        # Initialize content parser if needed
        content_parser = ContentParser() if parse_content else None
        
        try:
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
                        
                        # Parse full content if requested
                        content_length = None
                        content_parsed_at = None
                        content_parser_method = None
                        content_metadata = None
                        
                        if parse_content and content_parser:
                            logger.info(f"Parsing content for: {article.title}")
                            
                            full_content, metadata = await content_parser.extract_content(str(article.url))
                            
                            if full_content:
                                article_data['content'] = full_content
                                content_length = len(full_content)
                                content_parsed_at = datetime.utcnow().isoformat()
                                content_parser_method = metadata.get('method', 'unknown')
                                content_metadata = json.dumps(metadata)
                                
                                logger.info(f"Successfully parsed {content_length} characters for {article.title}")
                            else:
                                logger.warning(f"Failed to parse content for {article.title}")
                                content_metadata = json.dumps(metadata) if metadata else None
                        
                        # Map to existing database schema - use INSERT OR IGNORE since URL is unique
                        conn.execute("""
                            INSERT OR IGNORE INTO articles 
                            (title, url, content, summary, author, published_at, source, 
                             categories, metadata, content_length, content_parsed_at, 
                             content_parser_method, content_metadata, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            article_data['title'],
                            str(article_data['url']),
                            article_data['content'],
                            article_data['description'],  # Use description as summary
                            article_data['author'],
                            article_data['published_date'],  # This maps to published_at
                            article_data['source'],
                            article_data['tags'],  # This maps to categories
                            json.dumps({
                                'source_url': article_data['source_url'],
                                'original_metadata': content_metadata
                            }) if content_metadata else json.dumps({'source_url': article_data['source_url']}),
                            content_length,
                            content_parsed_at,
                            content_parser_method,
                            content_metadata
                        ))
                        
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error storing article {article.title}: {str(e)}")
                        continue
                
                conn.commit()
        
        finally:
            if content_parser:
                await content_parser.close()
        
        logger.info(f"Stored {stored_count} articles in database")
        return stored_count
    
    async def parse_missing_content(self, limit: int = 50) -> Dict[str, Any]:
        """
        Parse content for articles that don't have full content yet.
        
        Args:
            limit: Maximum number of articles to process
            
        Returns:
            Summary of parsing results
        """
        logger.info(f"Starting content parsing for up to {limit} articles")
        
        # Get articles without full content
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT id, title, url, source
                FROM articles 
                WHERE (content IS NULL OR content_length IS NULL OR content_length < 200)
                AND url IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            articles_to_parse = cursor.fetchall()
        
        if not articles_to_parse:
            logger.info("No articles found that need content parsing")
            return {"parsed": 0, "failed": 0, "message": "No articles to parse"}
        
        logger.info(f"Found {len(articles_to_parse)} articles to parse")
        
        parsed_count = 0
        failed_count = 0
        
        async with ContentParser() as parser:
            for article_row in articles_to_parse:
                try:
                    article_id = article_row['id']
                    url = article_row['url']
                    title = article_row['title']
                    
                    logger.info(f"Parsing content for: {title}")
                    
                    # Extract content
                    content, metadata = await parser.extract_content(url)
                    
                    # Update database
                    with sqlite3.connect(self.db_path) as conn:
                        if content:
                            conn.execute("""
                                UPDATE articles 
                                SET content = ?, 
                                    content_length = ?, 
                                    content_parsed_at = ?, 
                                    content_parser_method = ?,
                                    content_metadata = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (
                                content,
                                len(content),
                                datetime.utcnow().isoformat(),
                                metadata.get('method', 'unknown'),
                                json.dumps(metadata),
                                article_id
                            ))
                            parsed_count += 1
                            logger.info(f"Successfully parsed {len(content)} characters for {title}")
                        else:
                            # Store failure metadata
                            conn.execute("""
                                UPDATE articles 
                                SET content_parsed_at = ?, 
                                    content_parser_method = 'failed',
                                    content_metadata = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (
                                datetime.utcnow().isoformat(),
                                json.dumps(metadata) if metadata else None,
                                article_id
                            ))
                            failed_count += 1
                            logger.warning(f"Failed to parse content for {title}")
                        
                        conn.commit()
                    
                    # Small delay to be respectful to servers
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error parsing content for article {article_row['title']}: {str(e)}")
                    failed_count += 1
                    continue
        
        summary = {
            "parsed": parsed_count,
            "failed": failed_count,
            "total_processed": len(articles_to_parse),
            "message": f"Parsed {parsed_count} articles, {failed_count} failed"
        }
        
        logger.info(f"Content parsing completed: {summary['message']}")
        return summary
    
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


# Convenience functions for ingestion and content parsing
async def ingest_tech_news(parse_content: bool = False) -> Dict[str, Any]:
    """
    Convenience function to ingest tech news from all configured sources.
    
    Args:
        parse_content: Whether to parse full article content during ingestion
    
    Returns:
        Ingestion summary
    """
    async with RSSFeedIngester() as ingester:
        return await ingester.ingest_all_feeds(parse_content=parse_content)


async def parse_missing_content(limit: int = 50) -> Dict[str, Any]:
    """
    Parse content for articles that don't have full content yet.
    
    Args:
        limit: Maximum number of articles to process
    
    Returns:
        Parsing summary
    """
    async with RSSFeedIngester() as ingester:
        return await ingester.parse_missing_content(limit=limit)
