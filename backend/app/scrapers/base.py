"""
Base News Scraper
================
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import settings
from ..models import ArticleCreate

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all news scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.session: Optional[httpx.AsyncClient] = None
        self.stats = {
            "requests_made": 0,
            "articles_scraped": 0,
            "errors": 0,
            "last_fetch": None,
            "avg_response_time": 0.0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def setup(self):
        """Setup HTTP client with proper headers and timeouts"""
        timeout = httpx.Timeout(
            connect=settings.FETCH_TIMEOUT,
            read=settings.FETCH_TIMEOUT,
            write=settings.FETCH_TIMEOUT,
            pool=settings.FETCH_TIMEOUT
        )
        
        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.session = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        logger.info(f"Initialized scraper: {self.name}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.aclose()
            self.session = None
        
        logger.info(f"Cleaned up scraper: {self.name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_url(self, url: str) -> Optional[httpx.Response]:
        """Fetch URL with retry logic and rate limiting"""
        if not self.session:
            await self.setup()
        
        try:
            start_time = time.time()
            
            # Rate limiting
            await asyncio.sleep(settings.REQUEST_DELAY)
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Update stats
            self.stats["requests_made"] += 1
            response_time = time.time() - start_time
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["requests_made"] - 1) + response_time) /
                self.stats["requests_made"]
            )
            
            logger.debug(f"Fetched {url} in {response_time:.2f}s")
            return response
            
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            self.stats["errors"] += 1
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            self.stats["errors"] += 1
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def scrape(self) -> List[ArticleCreate]:
        """Main scraping method - to be implemented by subclasses"""
        try:
            start_time = time.time()
            
            articles = await self._scrape_implementation()
            
            # Update stats
            self.stats["articles_scraped"] = len(articles)
            self.stats["last_fetch"] = datetime.utcnow()
            
            scrape_time = time.time() - start_time
            logger.info(f"{self.name}: Scraped {len(articles)} articles in {scrape_time:.2f}s")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error in {self.name} scraper: {e}")
            self.stats["errors"] += 1
            return []
    
    @abstractmethod
    async def _scrape_implementation(self) -> List[ArticleCreate]:
        """Implementation-specific scraping logic"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        return {
            "name": self.name,
            "enabled": True,
            "last_fetch": self.stats["last_fetch"],
            "article_count": self.stats["articles_scraped"],
            "success_rate": self._calculate_success_rate(),
            "avg_response_time_ms": int(self.stats["avg_response_time"] * 1000),
            "total_requests": self.stats["requests_made"],
            "total_errors": self.stats["errors"]
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage"""
        total_requests = self.stats["requests_made"]
        if total_requests == 0:
            return 100.0
        
        success_rate = ((total_requests - self.stats["errors"]) / total_requests) * 100
        return round(success_rate, 2)