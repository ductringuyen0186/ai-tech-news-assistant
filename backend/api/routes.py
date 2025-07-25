"""
API Routes for AI Tech News Assistant
====================================

This module contains all API route definitions for the application.
Routes are organized by functionality and follow RESTful conventions.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from ingestion.rss_feeds import RSSFeedIngester, ingest_tech_news
from utils.logger import get_logger

logger = get_logger(__name__)

# Create the main router
router = APIRouter()


@router.get("/", tags=["API"])
async def api_info() -> Dict[str, Any]:
    """API information endpoint."""
    return {
        "message": "AI Tech News Assistant API v1",
        "endpoints": {
            "health": "/ping, /health",
            "news": "/news - Get latest articles",
            "news/ingest": "/news/ingest - Trigger RSS ingestion",
            "summarize": "/summarize (coming soon)",
            "search": "/search (coming soon)"
        }
    }


@router.get("/news", tags=["News"])
async def get_news(
    limit: int = Query(default=20, ge=1, le=100, description="Number of articles to return"),
    source: Optional[str] = Query(default=None, description="Filter by news source")
) -> Dict[str, Any]:
    """
    Get latest news articles from the database.
    
    Args:
        limit: Maximum number of articles to return (1-100)
        source: Optional source filter
        
    Returns:
        List of articles with metadata
    """
    try:
        logger.info(f"Fetching {limit} articles" + (f" from {source}" if source else ""))
        
        async with RSSFeedIngester() as ingester:
            articles = ingester.get_articles(limit=limit, source=source)
        
        return {
            "articles": articles,
            "count": len(articles),
            "limit": limit,
            "source_filter": source
        }
        
    except Exception as e:
        logger.error(f"Error fetching news articles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch articles")


@router.post("/news/ingest", tags=["News"])
async def trigger_news_ingestion() -> Dict[str, Any]:
    """
    Trigger RSS feed ingestion from all configured sources.
    
    This endpoint fetches the latest articles from RSS feeds and stores them
    in the database. It can be called manually or scheduled automatically.
    
    Returns:
        Ingestion summary with statistics
    """
    try:
        logger.info("Manual RSS ingestion triggered")
        
        summary = await ingest_tech_news()
        
        return {
            "message": "RSS ingestion completed successfully",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error during RSS ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail="RSS ingestion failed")


@router.get("/news/sources", tags=["News"])
async def get_news_sources() -> Dict[str, Any]:
    """
    Get information about configured news sources.
    
    Returns:
        List of news sources and their details
    """
    try:
        # Get sources from RSSFeedIngester
        ingester = RSSFeedIngester()
        sources = ingester.DEFAULT_SOURCES
        
        return {
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error fetching news sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch news sources")


@router.get("/news/stats", tags=["News"])
async def get_news_stats() -> Dict[str, Any]:
    """
    Get statistics about stored news articles.
    
    Returns:
        Database statistics and article counts by source
    """
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path("./data/articles.db")
        
        if not db_path.exists():
            return {
                "total_articles": 0,
                "sources": {},
                "database_exists": False
            }
        
        with sqlite3.connect(db_path) as conn:
            # Get total article count
            cursor = conn.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Get count by source
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count 
                FROM articles 
                GROUP BY source 
                ORDER BY count DESC
            """)
            source_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get date range
            cursor = conn.execute("""
                SELECT 
                    MIN(published_date) as earliest,
                    MAX(published_date) as latest
                FROM articles 
                WHERE published_date IS NOT NULL
            """)
            date_range = cursor.fetchone()
        
        return {
            "total_articles": total_articles,
            "sources": source_stats,
            "date_range": {
                "earliest": date_range[0],
                "latest": date_range[1]
            },
            "database_exists": True
        }
        
    except Exception as e:
        logger.error(f"Error fetching news statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


# Placeholder routes for future implementation
@router.post("/summarize", tags=["AI"])
async def summarize_article() -> Dict[str, str]:
    """Summarize an article using AI (placeholder)."""
    return {"message": "Summarization endpoint - coming soon"}


@router.get("/search", tags=["Search"])
async def search_articles() -> Dict[str, str]:
    """Search articles using semantic search (placeholder)."""
    return {"message": "Search endpoint - coming soon"}
