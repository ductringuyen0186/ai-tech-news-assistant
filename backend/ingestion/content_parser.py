"""
Content Parsing Module for AI Tech News Assistant
================================================

This module handles extracting clean, readable content from web articles.
It supports multiple parsing strategies and provides text normalization.

Features:
- BeautifulSoup HTML parsing
- Newspaper3k article extraction
- Text cleaning and normalization
- Content quality scoring
"""

import re
from typing import Optional, Dict, Any, Tuple

import httpx
from bs4 import BeautifulSoup, Comment
from newspaper import Article as NewspaperArticle

from utils.logger import get_logger

logger = get_logger(__name__)


class ContentParser:
    """Advanced content parsing and cleaning for news articles."""
    
    def __init__(self):
        """Initialize content parser."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        # Tags to remove completely
        self.REMOVE_TAGS = {
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'form', 'button', 'input', 'select', 'textarea',
            'iframe', 'embed', 'object', 'applet',
            'meta', 'link', 'title', 'head'
        }
        
        # Tags that typically contain ads or unwanted content
        self.AD_PATTERNS = [
            r'ad[-_]?container', r'advertisement', r'sponsored',
            r'popup', r'modal', r'newsletter', r'subscription',
            r'social[-_]?share', r'related[-_]?articles'
        ]
    
    async def extract_content(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract clean content from a web article.
        
        Args:
            url: Article URL to parse
            
        Returns:
            Tuple of (cleaned_content, metadata)
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Try Newspaper3k first (most reliable for news articles)
            content, metadata = await self._extract_with_newspaper(url)
            
            if content and len(content.strip()) > 200:
                logger.info(f"Successfully extracted {len(content)} characters with Newspaper3k")
                return content, metadata
            
            # Fallback to BeautifulSoup if Newspaper3k fails
            logger.info("Newspaper3k extraction insufficient, trying BeautifulSoup...")
            content, metadata = await self._extract_with_beautifulsoup(url)
            
            if content:
                logger.info(f"Successfully extracted {len(content)} characters with BeautifulSoup")
                return content, metadata
            
            logger.warning(f"Failed to extract meaningful content from {url}")
            return None, {"error": "Content extraction failed", "url": url}
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None, {"error": str(e), "url": url}
    
    async def _extract_with_newspaper(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract content using Newspaper3k library."""
        try:
            article = NewspaperArticle(url)
            
            # Download and parse the article
            article.download()
            article.parse()
            
            # Extract metadata
            metadata = {
                "method": "newspaper3k",
                "title": article.title,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "top_image": article.top_image,
                "keywords": article.keywords if hasattr(article, 'keywords') else [],
                "summary": article.summary if hasattr(article, 'summary') else None
            }
            
            # Get cleaned text
            content = article.text
            
            if content and len(content.strip()) > 50:
                # Clean and normalize the content
                cleaned_content = self._clean_text(content)
                return cleaned_content, metadata
            
            return None, metadata
            
        except Exception as e:
            logger.warning(f"Newspaper3k extraction failed for {url}: {str(e)}")
            return None, {"error": str(e), "method": "newspaper3k"}
    
    async def _extract_with_beautifulsoup(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract content using BeautifulSoup as fallback."""
        try:
            # Fetch the page
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            self._remove_unwanted_elements(soup)
            
            # Extract article content
            content = self._extract_article_text(soup)
            
            # Extract metadata
            metadata = {
                "method": "beautifulsoup",
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "charset": response.encoding or "utf-8"
            }
            
            if content and len(content.strip()) > 50:
                cleaned_content = self._clean_text(content)
                return cleaned_content, metadata
            
            return None, metadata
            
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return None, {"error": str(e), "method": "beautifulsoup"}
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove ads, scripts, and other unwanted elements."""
        # Remove script, style, and other unwanted tags
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove elements with ad-related class names or IDs
        for pattern in self.AD_PATTERNS:
            # Find by class
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            
            # Find by ID
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()
    
    def _extract_article_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main article text from parsed HTML."""
        # Common article container selectors (in order of preference)
        article_selectors = [
            'article',
            '[role="main"] article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.article-body',
            '.story-body',
            '.post-body',
            'main',
            '#content',
            '.main-content'
        ]
        
        for selector in article_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 200:  # Minimum content length
                    return text
        
        # Fallback: get text from body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        # Last resort: get all text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title from HTML."""
        # Try different title selectors
        selectors = ['h1', 'title', '.article-title', '.post-title', '.entry-title']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:
                    return title
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article description/summary from HTML meta tags."""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove common junk patterns
        junk_patterns = [
            r'Share this article.*?$',
            r'Follow us on.*?$',
            r'Subscribe to.*?$',
            r'Copyright.*?$',
            r'All rights reserved.*?$',
            r'Terms of use.*?$',
            r'Privacy policy.*?$'
        ]
        
        for pattern in junk_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Trim and return
        return text.strip()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
