"""
Reddit Scraper
=============
"""
import logging
from typing import List
from datetime import datetime
import re

from .base import BaseScraper
from ..models import ArticleCreate
from ..core.config import settings

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    """Production Reddit scraper for programming subreddits"""
    
    def __init__(self):
        super().__init__("Reddit Programming")
        self.subreddits = ["programming", "MachineLearning", "artificial", "datascience", "webdev"]
    
    async def _scrape_implementation(self) -> List[ArticleCreate]:
        """Scrape Reddit programming communities"""
        articles = []
        
        articles_per_subreddit = max(1, settings.MAX_ARTICLES_PER_SOURCE // len(self.subreddits))
        
        for subreddit in self.subreddits:
            subreddit_articles = await self._scrape_subreddit(subreddit, articles_per_subreddit)
            articles.extend(subreddit_articles)
            
            if len(articles) >= settings.MAX_ARTICLES_PER_SOURCE:
                break
        
        return articles[:settings.MAX_ARTICLES_PER_SOURCE]
    
    async def _scrape_subreddit(self, subreddit: str, limit: int) -> List[ArticleCreate]:
        """Scrape specific subreddit"""
        articles = []
        
        try:
            url = f"{settings.REDDIT_API_BASE}/{subreddit}/hot.json?limit={limit}"
            response = await self.fetch_url(url)
            
            if not response:
                logger.warning(f"Failed to fetch from r/{subreddit}")
                return articles
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                article = await self._process_reddit_post(post, subreddit)
                if article:
                    articles.append(article)
            
            logger.debug(f"Scraped {len(articles)} articles from r/{subreddit}")
            
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit}: {e}")
        
        return articles
    
    async def _process_reddit_post(self, post: dict, subreddit: str) -> ArticleCreate:
        """Process individual Reddit post"""
        try:
            post_data = post.get('data', {})
            
            title = post_data.get('title', '').strip()
            if not title:
                return None
            
            # Filter out certain post types
            if post_data.get('is_self') and not post_data.get('selftext'):
                return None
            
            # Skip deleted or removed posts
            if title.lower() in ['[deleted]', '[removed]']:
                return None
            
            # Create content
            content_parts = [title]
            
            # Add selftext if available
            selftext = post_data.get('selftext', '').strip()
            if selftext:
                # Clean markdown and limit length
                clean_text = self._clean_reddit_text(selftext)
                if clean_text:
                    content_parts.append(clean_text[:500])
            
            # Add subreddit context
            content_parts.append(f"Discussion on r/{subreddit}")
            
            content = ". ".join(content_parts)
            
            # Get URL (prefer external URL over Reddit permalink)
            post_url = post_data.get('url', '')
            permalink = f"https://reddit.com{post_data.get('permalink', '')}"
            
            # Use external URL if it's not a Reddit self-post
            if post_url and not post_url.startswith('https://www.reddit.com'):
                final_url = post_url
            else:
                final_url = permalink
            
            # Convert timestamp
            created_utc = post_data.get('created_utc', 0)
            published_at = datetime.fromtimestamp(created_utc) if created_utc else datetime.utcnow()
            
            return ArticleCreate(
                title=title,
                content=content,
                url=final_url,
                published_at=published_at,
                source=f"Reddit r/{subreddit}",
                source_id=post_data.get('id', '')
            )
            
        except Exception as e:
            logger.warning(f"Error processing Reddit post: {e}")
            return None
    
    def _clean_reddit_text(self, text: str) -> str:
        """Clean Reddit markdown and formatting"""
        if not text:
            return ""
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
        
        # Remove quotes and code blocks
        text = re.sub(r'^&gt;.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        
        # Clean whitespace
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()