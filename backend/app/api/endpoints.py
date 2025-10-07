"""
API Endpoints
============
"""
import time
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse

from ..models import (
    Article, ArticleList, SearchRequest, SearchResponse, SearchResult,
    SummarizeRequest, SummaryResponse, HealthResponse, SystemStats
)
from ..services.database import db_service
from ..services.scraping import scraping_manager
from ..core.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Application start time for uptime calculation
app_start_time = datetime.utcnow()


@router.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "operational",
        "features": [
            "real_time_news_scraping",
            "semantic_search",
            "ai_summarization",
            "multiple_sources",
            "production_ready"
        ],
        "sources": ["Hacker News", "Reddit Programming", "GitHub Trending"],
        "documentation": "/docs",
        "health_check": "/health"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    
    # Check database connectivity
    try:
        article_count = db_service.get_article_count()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
        article_count = 0
    
    # Check scraper status
    scraper_stats = scraping_manager.get_scraper_stats()
    scrapers_healthy = all(stat["success_rate"] > 50 for stat in scraper_stats if stat.get("total_requests", 0) > 0)
    
    components = {
        "database": db_status,
        "scrapers": "healthy" if scrapers_healthy else "degraded",
        "api": "healthy",
        "total_articles": article_count
    }
    
    overall_status = "healthy" if all(status in ["healthy", "degraded"] for status in components.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.VERSION,
        components=components,
        uptime_seconds=int(uptime)
    )


@router.get("/articles", response_model=dict)
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Articles per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    background_tasks: BackgroundTasks = None
):
    """Get articles with pagination and filtering"""
    try:
        # Auto-fetch if cache is stale
        if scraping_manager.should_fetch_news():
            logger.info("Cache is stale, triggering background news fetch")
            background_tasks.add_task(scraping_manager.fetch_all_news)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Apply source filter
        source_filter = [source] if source else None
        
        # Get articles
        articles = db_service.get_articles(
            limit=per_page,
            offset=offset,
            source_filter=source_filter
        )
        
        # Get total count for pagination
        total_articles = db_service.get_article_count(source_filter=source_filter)
        
        # Calculate pagination info
        has_next = (offset + per_page) < total_articles
        has_prev = page > 1
        
        return {
            "success": True,
            "articles": articles,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_articles,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "last_fetch": scraping_manager.last_successful_fetch.isoformat() if scraping_manager.last_successful_fetch else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch articles")


@router.post("/search", response_model=SearchResponse)
async def search_articles(request: SearchRequest):
    """Search articles with relevance scoring"""
    start_time = time.time()
    
    try:
        results = db_service.search_articles(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            source_filter=request.source_filter
        )
        
        # Convert to response format
        search_results = [
            SearchResult(
                article=result["article"],
                relevance_score=result["relevance_score"],
                highlight_snippet=result["highlight_snippet"]
            )
            for result in results
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            took_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_article(request: SummarizeRequest):
    """Summarize article content with AI or extractive methods"""
    start_time = time.time()
    
    try:
        # Simple extractive summarization (can be enhanced with AI)
        sentences = request.text.split('. ')
        
        if len(sentences) >= 3:
            # Take first two sentences for summary
            summary = sentences[0] + '. ' + sentences[1] + '.'
            method = "extractive_multi_sentence"
        elif len(sentences) >= 2:
            summary = sentences[0] + '. ' + sentences[1] + '.'
            method = "extractive_dual_sentence"
        else:
            # Single sentence or short text
            summary = sentences[0] + '.' if sentences else request.text[:request.max_length]
            method = "extractive_single"
        
        # Trim to max length
        if len(summary) > request.max_length:
            words = summary.split()
            summary = ' '.join(words[:20]) + '...'
            method += "_truncated"
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # TODO: Integrate with Ollama for AI summarization when use_ai=True
        
        return SummaryResponse(
            summary=summary,
            method=method,
            original_length=len(request.text),
            summary_length=len(summary),
            processing_time_ms=processing_time,
            confidence_score=0.8  # Static for now
        )
        
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed")


@router.post("/fetch-news", response_model=dict)
async def trigger_news_fetch(background_tasks: BackgroundTasks):
    """Manually trigger news fetching from all sources"""
    if scraping_manager.scraping_in_progress:
        raise HTTPException(
            status_code=409,
            detail="News fetching already in progress"
        )
    
    # Start background task
    background_tasks.add_task(scraping_manager.fetch_all_news)
    
    return {
        "success": True,
        "message": "News fetching started in background",
        "estimated_duration": "30-60 seconds",
        "sources": list(scraping_manager.scrapers.keys())
    }


@router.post("/fetch-news/{source_name}", response_model=dict)
async def fetch_from_specific_source(source_name: str, background_tasks: BackgroundTasks):
    """Fetch news from specific source"""
    if source_name not in scraping_manager.scrapers:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown source: {source_name}"
        )
    
    # Start background task
    background_tasks.add_task(scraping_manager.fetch_from_source, source_name)
    
    return {
        "success": True,
        "message": f"Fetching news from {source_name} in background",
        "source": source_name
    }


@router.get("/sources", response_model=dict)
async def get_news_sources():
    """Get information about available news sources"""
    scraper_stats = scraping_manager.get_scraper_stats()
    
    # Get database stats per source
    db_stats = db_service.get_sources_stats()
    
    # Combine scraper and database stats
    sources = []
    for scraper_stat in scraper_stats:
        # Find matching database stat
        db_stat = next(
            (stat for stat in db_stats if stat["name"] == scraper_stat["name"]),
            {"article_count": 0, "last_fetch": None, "avg_views": 0.0}
        )
        
        sources.append({
            "name": scraper_stat["name"],
            "enabled": scraper_stat["enabled"],
            "last_fetch": scraper_stat["last_fetch"],
            "article_count": db_stat["article_count"],
            "success_rate": scraper_stat["success_rate"],
            "avg_response_time_ms": scraper_stat["avg_response_time_ms"],
            "avg_views": db_stat["avg_views"]
        })
    
    return {
        "success": True,
        "sources": sources,
        "total_sources": len(sources)
    }


@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        # Get database stats
        total_articles = db_service.get_article_count()
        
        # Get scraper stats
        scraper_stats = scraping_manager.get_scraper_stats()
        manager_stats = scraping_manager.get_manager_stats()
        
        # Calculate uptime
        uptime = int((datetime.utcnow() - app_start_time).total_seconds())
        
        # Convert scraper stats to NewsSource format
        sources = []
        for stat in scraper_stats:
            sources.append({
                "name": stat["name"],
                "enabled": stat["enabled"],
                "last_fetch": stat["last_fetch"],
                "article_count": stat["article_count"],
                "success_rate": stat["success_rate"],
                "avg_response_time_ms": stat["avg_response_time_ms"]
            })
        
        return SystemStats(
            total_articles=total_articles,
            sources=sources,
            cache_size=total_articles,  # Simplified
            last_fetch=manager_stats["last_successful_fetch"],
            uptime_seconds=uptime,
            requests_per_hour=0  # TODO: Implement request tracking
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system statistics")