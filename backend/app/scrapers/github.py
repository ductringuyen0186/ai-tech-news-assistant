"""
GitHub Trending Scraper
======================
"""
import logging
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..models import ArticleCreate
from ..core.config import settings

logger = logging.getLogger(__name__)


class GitHubTrendingScraper(BaseScraper):
    """Production GitHub Trending scraper"""
    
    def __init__(self):
        super().__init__("GitHub Trending")
        self.trending_url = settings.GITHUB_TRENDING_URL
        self.languages = ["", "javascript", "python", "typescript", "go", "rust"]  # "" = all languages
    
    async def _scrape_implementation(self) -> List[ArticleCreate]:
        """Scrape GitHub trending repositories"""
        articles = []
        
        articles_per_language = max(1, settings.MAX_ARTICLES_PER_SOURCE // len(self.languages))
        
        for language in self.languages:
            language_articles = await self._scrape_trending_language(language, articles_per_language)
            articles.extend(language_articles)
            
            if len(articles) >= settings.MAX_ARTICLES_PER_SOURCE:
                break
        
        return articles[:settings.MAX_ARTICLES_PER_SOURCE]
    
    async def _scrape_trending_language(self, language: str, limit: int) -> List[ArticleCreate]:
        """Scrape trending repositories for specific language"""
        articles = []
        
        try:
            url = self.trending_url
            if language:
                url = f"{url}/{language}"
            
            response = await self.fetch_url(url)
            
            if not response:
                logger.warning(f"Failed to fetch GitHub trending for {language or 'all languages'}")
                return articles
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find repository containers
            repo_containers = soup.find_all('article', class_='Box-row')[:limit]
            
            for container in repo_containers:
                article = await self._process_github_repo(container, language)
                if article:
                    articles.append(article)
            
            logger.debug(f"Scraped {len(articles)} repos from GitHub trending ({language or 'all'})")
            
        except Exception as e:
            logger.error(f"Error scraping GitHub trending {language}: {e}")
        
        return articles
    
    async def _process_github_repo(self, container, language: str) -> ArticleCreate:
        """Process individual GitHub repository"""
        try:
            # Extract repository name and URL
            title_elem = container.find('h2', class_='h3')
            if not title_elem:
                return None
            
            repo_link = title_elem.find('a')
            if not repo_link:
                return None
            
            repo_name = repo_link.get_text().strip().replace('\\n', '').replace(' ', '')
            repo_url = f"https://github.com{repo_link.get('href', '')}"
            
            # Extract description
            description_elem = container.find('p', class_='col-9')
            description = ""
            if description_elem:
                description = description_elem.get_text().strip()
            
            # Extract language information
            language_elem = container.find('span', {'itemprop': 'programmingLanguage'})
            repo_language = ""
            if language_elem:
                repo_language = language_elem.get_text().strip()
            
            # Extract stars and forks if available
            stats_info = ""
            stats_elements = container.find_all('a', class_='Link--muted')
            for stats_elem in stats_elements:
                if 'stargazers' in stats_elem.get('href', ''):
                    stars = stats_elem.get_text().strip()
                    stats_info += f" ⭐ {stars}"
                elif 'network/members' in stats_elem.get('href', ''):
                    forks = stats_elem.get_text().strip()
                    stats_info += f" 🍴 {forks}"
            
            # Extract today's stars if available
            today_stars_elem = container.find('span', class_='d-inline-block')
            if today_stars_elem and '★' in today_stars_elem.get_text():
                today_stars = today_stars_elem.get_text().strip()
                stats_info += f" ({today_stars} today)"
            
            # Create title and content
            title = f"Trending: {repo_name}"
            if repo_language:
                title += f" ({repo_language})"
            
            content_parts = []
            if description:
                content_parts.append(description)
            
            content_parts.append(f"This {repo_language or 'repository'} project is currently trending on GitHub")
            
            if stats_info:
                content_parts.append(f"Repository stats: {stats_info.strip()}")
            
            content_parts.append("Trending repositories often showcase innovative solutions, popular tools, or emerging technologies in the developer community")
            
            content = ". ".join(content_parts)
            
            return ArticleCreate(
                title=title,
                content=content,
                url=repo_url,
                published_at=datetime.utcnow(),
                source="GitHub Trending",
                source_id=repo_name.replace('/', '_')
            )
            
        except Exception as e:
            logger.warning(f"Error processing GitHub repo: {e}")
            return None