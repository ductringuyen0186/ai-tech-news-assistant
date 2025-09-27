"""
Hacker News Scraper
==================
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import hashlib

from .base import BaseScraper
from ..models import ArticleCreate
from ..core.config import settings

logger = logging.getLogger(__name__)


class HackerNewsScraper(BaseScraper):
    """Production Hacker News scraper using official API"""
    
    def __init__(self):
        super().__init__("Hacker News")
        self.api_base = settings.HACKER_NEWS_API_BASE
    
    async def _scrape_implementation(self) -> List[ArticleCreate]:
        """Scrape Hacker News using official API"""
        articles = []
        
        try:
            # Fetch top story IDs
            top_stories_url = f"{self.api_base}/topstories.json"
            response = await self.fetch_url(top_stories_url)
            
            if not response:
                logger.error("Failed to fetch top stories from Hacker News")
                return articles
            
            story_ids = response.json()[:settings.MAX_ARTICLES_PER_SOURCE]
            logger.info(f"Fetching {len(story_ids)} stories from Hacker News")
            
            # Fetch individual stories
            for story_id in story_ids:
                article = await self._fetch_story(story_id)
                if article:
                    articles.append(article)
                
                # Rate limiting between requests
                if len(articles) % 5 == 0:
                    logger.debug(f"Processed {len(articles)} stories...")
            
            logger.info(f"Successfully scraped {len(articles)} articles from Hacker News")
            
        except Exception as e:
            logger.error(f"Error scraping Hacker News: {e}")
        
        return articles
    
    async def _fetch_story(self, story_id: int) -> ArticleCreate:
        """Fetch individual story details"""
        try:
            story_url = f"{self.api_base}/item/{story_id}.json"
            response = await self.fetch_url(story_url)
            
            if not response:
                return None
            
            story_data = response.json()
            
            # Validate story data
            if not story_data or story_data.get('type') != 'story':
                return None
            
            title = story_data.get('title', '').strip()
            if not title:
                return None
            
            # Get story URL or use HN discussion URL
            story_url = story_data.get('url') or f"https://news.ycombinator.com/item?id={story_id}"
            
            # Create content from title and any text
            content_parts = [title]
            
            if story_data.get('text'):
                # Clean HTML tags from text
                import re
                clean_text = re.sub('<.*?>', '', story_data['text'])
                content_parts.append(clean_text[:500])
            
            content = ". ".join(content_parts)
            
            # Convert timestamp
            timestamp = story_data.get('time', 0)
            published_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.utcnow()
            
            return ArticleCreate(
                title=title,
                content=content,
                url=story_url,
                published_at=published_at,
                source="Hacker News",
                source_id=str(story_id)
            )
            
        except Exception as e:
            logger.warning(f"Error fetching HN story {story_id}: {e}")
            return None