"""
Generic RSS Feed Scraper
========================
"""
import logging
import feedparser
from typing import List
from datetime import datetime
from dateutil import parser as date_parser

from .base import BaseScraper
from ..models import ArticleCreate
from ..core.config import settings

logger = logging.getLogger(__name__)


class RSSFeedScraper(BaseScraper):
    """Generic RSS/Atom feed scraper"""

    def __init__(self, name: str, feed_url: str):
        super().__init__(name)
        self.feed_url = feed_url

    async def _scrape_implementation(self) -> List[ArticleCreate]:
        """Scrape RSS feed"""
        articles = []

        try:
            # Fetch feed
            response = await self.fetch_url(self.feed_url)

            if not response:
                logger.error(f"Failed to fetch feed: {self.feed_url}")
                return articles

            # Parse feed
            feed_content = response.text
            feed = feedparser.parse(feed_content)

            if not feed.entries:
                logger.warning(f"No entries found in feed: {self.feed_url}")
                return articles

            logger.info(f"Found {len(feed.entries)} entries in {self.name}")

            # Process entries (limit to max articles)
            for entry in feed.entries[:settings.MAX_ARTICLES_PER_SOURCE]:
                article = self._parse_entry(entry)
                if article:
                    articles.append(article)

            logger.info(f"Successfully scraped {len(articles)} articles from {self.name}")

        except Exception as e:
            logger.error(f"Error scraping RSS feed {self.name}: {e}")

        return articles

    def _parse_entry(self, entry) -> ArticleCreate:
        """Parse RSS entry to ArticleCreate"""
        try:
            # Get title
            title = entry.get('title', '').strip()
            if not title:
                return None

            # Get link/URL
            url = entry.get('link', '').strip()
            if not url:
                return None

            # Get content/description
            content = (
                entry.get('summary', '') or
                entry.get('description', '') or
                entry.get('content', [{}])[0].get('value', '') or
                title
            )

            # Clean HTML from content
            import re
            content = re.sub('<.*?>', '', content).strip()

            # Get published date
            published_str = entry.get('published') or entry.get('updated')
            if published_str:
                try:
                    published_at = date_parser.parse(published_str)
                except:
                    published_at = datetime.utcnow()
            else:
                published_at = datetime.utcnow()

            # Get source ID if available
            source_id = entry.get('id') or url

            return ArticleCreate(
                title=title,
                content=content[:2000],  # Limit content length
                url=url,
                published_at=published_at,
                source=self.name,
                source_id=source_id
            )

        except Exception as e:
            logger.warning(f"Error parsing RSS entry: {e}")
            return None


# Predefined tech news RSS feeds
class TechCrunchScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "TechCrunch",
            "https://techcrunch.com/feed/"
        )


class TheVergeScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "The Verge",
            "https://www.theverge.com/rss/index.xml"
        )


class ArsTechnicaScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "Ars Technica",
            "https://feeds.arstechnica.com/arstechnica/index"
        )


class WiredScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "Wired",
            "https://www.wired.com/feed/rss"
        )


class VentureBeatScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "VentureBeat",
            "https://venturebeat.com/feed/"
        )


class MITTechReviewScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "MIT Technology Review",
            "https://www.technologyreview.com/feed/"
        )


# AI/ML specific feeds
class OpenAIBlogScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "OpenAI Blog",
            "https://openai.com/blog/rss/"
        )


class GoogleAIBlogScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "Google AI Blog",
            "https://ai.googleblog.com/feeds/posts/default"
        )


class AnthropicNewsScraper(RSSFeedScraper):
    def __init__(self):
        super().__init__(
            "Anthropic News",
            "https://www.anthropic.com/news/rss.xml"
        )
