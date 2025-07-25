"""
API Routes for AI Tech News Assistant
====================================

This module contains all API route definitions for the application.
Routes are organized by functionality and follow RESTful conventions.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from ingestion.rss_feeds import RSSFeedIngester, ingest_tech_news, parse_missing_content
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
            "news/parse": "/news/parse - Parse content for existing articles",
            "news/sources": "/news/sources - Get configured news sources",
            "news/stats": "/news/stats - Get article statistics",
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
async def trigger_news_ingestion(
    parse_content: bool = Query(default=False, description="Whether to parse full article content (slower)")
) -> Dict[str, Any]:
    """
    Trigger RSS feed ingestion from all configured sources.
    
    This endpoint fetches the latest articles from RSS feeds and stores them
    in the database. Optionally parses full article content.
    
    Args:
        parse_content: Whether to extract full article content during ingestion
    
    Returns:
        Ingestion summary with statistics
    """
    try:
        logger.info(f"Manual RSS ingestion triggered (parse_content={parse_content})")
        
        summary = await ingest_tech_news(parse_content=parse_content)
        
        return {
            "message": "RSS ingestion completed successfully",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error during RSS ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail="RSS ingestion failed")


@router.post("/news/parse", tags=["News"])
async def trigger_content_parsing(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of articles to parse")
) -> Dict[str, Any]:
    """
    Parse full content for articles that don't have it yet.
    
    This endpoint extracts clean, readable content from article URLs for
    articles that only have RSS summaries. Useful for retroactively parsing
    content or handling failed parsing attempts.
    
    Args:
        limit: Maximum number of articles to process (1-200)
    
    Returns:
        Content parsing summary with statistics
    """
    try:
        logger.info(f"Manual content parsing triggered for up to {limit} articles")
        
        summary = await parse_missing_content(limit=limit)
        
        return {
            "message": "Content parsing completed",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error during content parsing: {str(e)}")
        raise HTTPException(status_code=500, detail="Content parsing failed")


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
            
            # Get content parsing statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN content_length > 200 THEN 1 END) as with_content,
                    COUNT(CASE WHEN content_parsed_at IS NOT NULL THEN 1 END) as parse_attempted,
                    AVG(content_length) as avg_content_length
                FROM articles
            """)
            content_stats = cursor.fetchone()
            
            # Get parsing method breakdown
            cursor = conn.execute("""
                SELECT content_parser_method, COUNT(*) as count
                FROM articles 
                WHERE content_parser_method IS NOT NULL
                GROUP BY content_parser_method
            """)
            parser_method_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
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
            "content_stats": {
                "total_articles": content_stats[0],
                "with_full_content": content_stats[1],
                "parse_attempted": content_stats[2],
                "avg_content_length": round(content_stats[3], 2) if content_stats[3] else 0,
                "parser_methods": parser_method_stats
            },
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
