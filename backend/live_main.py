"""
AI Tech News Assistant Backend - Live RSS Feeds
==============================================

Enhanced backend that fetches real tech news from multiple RSS sources.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn
from typing import List, Dict, Any, Optional
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import hashlib
from urllib.parse import urljoin
import asyncio
import threading
import time
from dateutil import parser as date_parser

# Create FastAPI app
app = FastAPI(
    title="AI Tech News Assistant",
    description="Live RSS feed aggregator for tech news",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RSS Feed Sources
RSS_FEEDS = {
    "TechCrunch": {
        "url": "https://techcrunch.com/feed/",
        "category": "Startup & Venture"
    },
    "The Verge": {
        "url": "https://www.theverge.com/rss/index.xml",
        "category": "Consumer Tech"
    },
    "Ars Technica": {
        "url": "http://feeds.arstechnica.com/arstechnica/index",
        "category": "Deep Tech"
    },
    "MIT Technology Review": {
        "url": "https://www.technologyreview.com/feed/",
        "category": "Research & Innovation"
    },
    "Wired": {
        "url": "https://www.wired.com/feed/rss",
        "category": "Future Tech"
    },
    "VentureBeat": {
        "url": "https://venturebeat.com/feed/",
        "category": "AI & Business"
    },
    "AI News": {
        "url": "https://artificialintelligence-news.com/feed/",
        "category": "Artificial Intelligence"
    }
}

# Global storage for articles
articles_storage = []
last_update = None
update_lock = threading.Lock()

def clean_text(text: str) -> str:
    """Clean and format text content"""
    if not text:
        return ""
    
    # Remove HTML tags
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Limit length for summaries
    if len(text) > 500:
        text = text[:497] + "..."
    
    return text

def estimate_reading_time(text: str) -> int:
    """Estimate reading time in minutes"""
    words = len(text.split())
    # Average reading speed: 200 words per minute
    return max(1, round(words / 200))

def generate_article_id(title: str, url: str) -> str:
    """Generate unique ID for article"""
    content = f"{title}{url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def parse_date(date_str: str) -> datetime:
    """Parse various date formats"""
    try:
        parsed_date = date_parser.parse(date_str)
        # Convert to naive datetime if it has timezone info
        if parsed_date.tzinfo is not None:
            parsed_date = parsed_date.replace(tzinfo=None)
        return parsed_date
    except:
        return datetime.now()

def fetch_single_feed(feed_name: str, feed_info: dict) -> List[dict]:
    """Fetch articles from a single RSS feed"""
    articles = []
    try:
        print(f"📡 Fetching {feed_name}...")
        
        # Set user agent to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch feed with timeout
        response = requests.get(feed_info["url"], headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:10]:  # Limit to 10 articles per feed
            try:
                # Parse published date
                pub_date = datetime.now()
                if hasattr(entry, 'published'):
                    pub_date = parse_date(entry.published)
                elif hasattr(entry, 'updated'):
                    pub_date = parse_date(entry.updated)
                
                # Skip very old articles (older than 30 days)
                if (datetime.now() - pub_date).days > 30:
                    continue
                
                # Extract summary
                summary = ""
                if hasattr(entry, 'summary'):
                    summary = clean_text(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_text(entry.description)
                
                # Create article object
                article = {
                    "id": generate_article_id(entry.title, entry.link),
                    "title": clean_text(entry.title),
                    "summary": summary or "Summary not available",
                    "url": entry.link,
                    "source": feed_name,
                    "published_at": pub_date.isoformat(),
                    "category": feed_info["category"],
                    "reading_time": estimate_reading_time(summary),
                    "sentiment": "neutral"  # Could be enhanced with sentiment analysis
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"❌ Error parsing entry from {feed_name}: {e}")
                continue
                
        print(f"✅ {feed_name}: {len(articles)} articles")
        
    except Exception as e:
        print(f"❌ Error fetching {feed_name}: {e}")
    
    return articles

def update_articles():
    """Update articles from all RSS feeds"""
    global articles_storage, last_update
    
    with update_lock:
        print("🔄 Starting RSS feed update...")
        all_articles = []
        
        # Fetch from all feeds
        for feed_name, feed_info in RSS_FEEDS.items():
            articles = fetch_single_feed(feed_name, feed_info)
            all_articles.extend(articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        # Sort by published date (newest first)
        unique_articles.sort(key=lambda x: x["published_at"], reverse=True)
        
        # Update global storage
        articles_storage = unique_articles[:100]  # Keep latest 100 articles
        last_update = datetime.now()
        
        print(f"✅ Update complete: {len(articles_storage)} unique articles")

def background_updater():
    """Background thread to update feeds periodically"""
    while True:
        try:
            update_articles()
            # Wait 30 minutes before next update
            time.sleep(1800)
        except Exception as e:
            print(f"❌ Background update error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

# Start background updater
update_thread = threading.Thread(target=background_updater, daemon=True)
update_thread.start()

# Initial update
update_articles()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Tech News Assistant API - Live RSS Feeds",
        "version": "2.0.0",
        "status": "running",
        "last_update": last_update.isoformat() if last_update else None,
        "total_articles": len(articles_storage),
        "feeds": len(RSS_FEEDS)
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "articles_count": len(articles_storage),
        "last_update": last_update.isoformat() if last_update else None,
        "feeds_configured": len(RSS_FEEDS)
    }

@app.get("/api/v1/news/stats")
async def get_news_stats():
    """Get news statistics"""
    categories = {}
    sources = {}
    
    for article in articles_storage:
        # Count categories
        category = article["category"]
        categories[category] = categories.get(category, 0) + 1
        
        # Count sources
        source = article["source"]
        sources[source] = sources.get(source, 0) + 1
    
    return {
        "total_articles": len(articles_storage),
        "categories": categories,
        "sources": sources,
        "last_updated": last_update.isoformat() if last_update else None,
        "update_frequency": "30 minutes"
    }

@app.get("/api/v1/news/articles")
async def get_articles(limit: int = 10, category: str = None, search: str = None, source: str = None):
    """Get news articles with optional filtering"""
    articles = articles_storage.copy()
    
    # Filter by category if provided
    if category and category.lower() != "all":
        articles = [a for a in articles if category.lower() in a["category"].lower()]
    
    # Filter by source if provided
    if source and source.lower() != "all":
        articles = [a for a in articles if source.lower() in a["source"].lower()]
    
    # Simple search if provided
    if search:
        search_lower = search.lower()
        articles = [
            a for a in articles 
            if search_lower in a["title"].lower() or search_lower in a["summary"].lower()
        ]
    
    # Limit results
    articles = articles[:limit]
    
    return {
        "articles": articles,
        "total": len(articles),
        "limit": limit,
        "filters": {
            "category": category,
            "source": source,
            "search": search
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/news/articles/{article_id}")
async def get_article(article_id: str):
    """Get a specific article by ID"""
    article = next((a for a in articles_storage if a["id"] == article_id), None)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article

@app.get("/api/v1/news/categories")
async def get_categories():
    """Get available categories"""
    categories = list(set(article["category"] for article in articles_storage))
    return {
        "categories": sorted(categories),
        "count": len(categories)
    }

@app.get("/api/v1/news/sources")
async def get_sources():
    """Get available sources"""
    sources = list(set(article["source"] for article in articles_storage))
    return {
        "sources": sorted(sources),
        "count": len(sources)
    }

@app.post("/api/v1/news/search")
async def search_articles(query: Dict[str, Any]):
    """Advanced search for articles"""
    search_term = query.get("query", "")
    category = query.get("category")
    source = query.get("source")
    limit = query.get("limit", 10)
    
    return await get_articles(limit=limit, category=category, source=source, search=search_term)

@app.post("/api/v1/news/refresh")
async def refresh_feeds(background_tasks: BackgroundTasks):
    """Manually trigger feed refresh"""
    background_tasks.add_task(update_articles)
    return {
        "message": "Feed refresh triggered",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting AI Tech News Assistant - Live RSS Backend")
    print(f"📡 Configured {len(RSS_FEEDS)} RSS feeds")
    print("🔄 Auto-updates every 30 minutes")
    print("🌐 Frontend proxy: http://localhost:3000")
    print("📚 API docs: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
