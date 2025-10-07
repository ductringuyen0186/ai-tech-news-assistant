"""
Scraper Manager
==============
"""
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..scrapers.hackernews import HackerNewsScraper
from ..scrapers.reddit import RedditScraper
from ..scrapers.github import GitHubTrendingScraper
from ..scrapers.rss_scraper import (
    TechCrunchScraper, TheVergeScraper, ArsTechnicaScraper,
    WiredScraper, VentureBeatScraper, MITTechReviewScraper,
    OpenAIBlogScraper, GoogleAIBlogScraper
)
from ..models import ArticleCreate
from ..services.database import db_service
from ..services.ai_service import ai_service
from ..core.config import settings

logger = logging.getLogger(__name__)


class ScrapingManager:
    """Manages all news scrapers with concurrent execution and error handling"""
    
    def __init__(self):
        self.scrapers = {
            # Original scrapers
            "hackernews": HackerNewsScraper(),
            "reddit": RedditScraper(),
            "github": GitHubTrendingScraper(),
            # Major tech news sites
            "techcrunch": TechCrunchScraper(),
            "theverge": TheVergeScraper(),
            "arstechnica": ArsTechnicaScraper(),
            "wired": WiredScraper(),
            "venturebeat": VentureBeatScraper(),
            "mittr": MITTechReviewScraper(),
            # AI/ML specific sources
            "openai": OpenAIBlogScraper(),
            "googleai": GoogleAIBlogScraper(),
        }

        self.last_successful_fetch = None
        self.total_articles_fetched = 0
        self.scraping_in_progress = False
        self.enable_ai_enrichment = True  # Toggle AI enrichment
    
    async def fetch_all_news(self) -> Dict[str, Any]:
        """Fetch news from all sources concurrently"""
        if self.scraping_in_progress:
            return {
                "success": False,
                "message": "Scraping already in progress",
                "articles_added": 0
            }
        
        self.scraping_in_progress = True
        start_time = datetime.utcnow()
        
        try:
            logger.info("Starting comprehensive news fetch from all sources")
            
            # Run all scrapers concurrently
            tasks = []
            for scraper_name, scraper in self.scrapers.items():
                tasks.append(self._run_scraper_safely(scraper_name, scraper))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            total_articles = 0
            total_new_articles = 0
            scraper_results = {}
            
            for i, result in enumerate(results):
                scraper_name = list(self.scrapers.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Scraper {scraper_name} failed: {result}")
                    scraper_results[scraper_name] = {
                        "success": False,
                        "articles": 0,
                        "new_articles": 0,
                        "error": str(result)
                    }
                else:
                    articles, new_articles = result
                    total_articles += len(articles)
                    total_new_articles += new_articles
                    
                    scraper_results[scraper_name] = {
                        "success": True,
                        "articles": len(articles),
                        "new_articles": new_articles,
                        "error": None
                    }
            
            # Update global stats
            self.last_successful_fetch = datetime.utcnow()
            self.total_articles_fetched += total_new_articles
            
            fetch_duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"News fetch completed: {total_new_articles} new articles in {fetch_duration:.2f}s")
            
            return {
                "success": True,
                "message": f"Successfully fetched {total_new_articles} new articles",
                "articles_added": total_new_articles,
                "total_articles_processed": total_articles,
                "duration_seconds": fetch_duration,
                "scraper_results": scraper_results,
                "last_fetch": self.last_successful_fetch.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during news fetch: {e}")
            return {
                "success": False,
                "message": f"News fetch failed: {str(e)}",
                "articles_added": 0
            }
        finally:
            self.scraping_in_progress = False
    
    async def _run_scraper_safely(self, scraper_name: str, scraper) -> tuple[List[ArticleCreate], int]:
        """Run individual scraper with error handling"""
        try:
            async with scraper:
                articles = await scraper.scrape()
                
                if not articles:
                    logger.warning(f"No articles from {scraper_name}")
                    return [], 0
                
                # Save articles to database with AI enrichment
                new_articles_count = 0

                for article in articles:
                    try:
                        # AI enrichment if enabled
                        if self.enable_ai_enrichment:
                            enrichment = await ai_service.enrich_article(
                                article.title,
                                article.content
                            )

                            # Create enriched article data
                            article_dict = article.dict()
                            article_dict.update({
                                'ai_summary': enrichment.get('ai_summary'),
                                'categories': enrichment.get('categories', []),
                                'keywords': enrichment.get('keywords', []),
                                'sentiment': enrichment.get('sentiment')
                            })

                            saved_article = db_service.create_article_enriched(article_dict)
                        else:
                            saved_article = db_service.create_article(article)

                        if saved_article:
                            new_articles_count += 1

                    except Exception as e:
                        logger.warning(f"Error saving article from {scraper_name}: {e}")
                        continue

                logger.info(f"{scraper_name}: {new_articles_count}/{len(articles)} new articles saved")
                return articles, new_articles_count
                
        except Exception as e:
            logger.error(f"Error in scraper {scraper_name}: {e}")
            return [], 0
    
    async def fetch_from_source(self, source_name: str) -> Dict[str, Any]:
        """Fetch news from specific source"""
        if source_name not in self.scrapers:
            return {
                "success": False,
                "message": f"Unknown source: {source_name}",
                "articles_added": 0
            }
        
        try:
            scraper = self.scrapers[source_name]
            articles, new_articles = await self._run_scraper_safely(source_name, scraper)
            
            return {
                "success": True,
                "message": f"Fetched {new_articles} new articles from {source_name}",
                "articles_added": new_articles,
                "total_articles_processed": len(articles)
            }
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            return {
                "success": False,
                "message": f"Failed to fetch from {source_name}: {str(e)}",
                "articles_added": 0
            }
    
    def get_scraper_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all scrapers"""
        stats = []
        
        for scraper_name, scraper in self.scrapers.items():
            scraper_stats = scraper.get_stats()
            stats.append(scraper_stats)
        
        return stats
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get scraping manager statistics"""
        return {
            "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            "total_articles_fetched": self.total_articles_fetched,
            "scraping_in_progress": self.scraping_in_progress,
            "available_sources": list(self.scrapers.keys()),
            "scrapers_count": len(self.scrapers)
        }
    
    def should_fetch_news(self) -> bool:
        """Check if news should be fetched based on cache expiry"""
        if not self.last_successful_fetch:
            return True
        
        cache_expiry = timedelta(hours=settings.CACHE_EXPIRY_HOURS)
        return datetime.utcnow() - self.last_successful_fetch > cache_expiry


# Global scraping manager instance
scraping_manager = ScrapingManager()