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
async def summarize_article(
    article_id: Optional[int] = Query(default=None, description="Database article ID to summarize"),
    url: Optional[str] = Query(default=None, description="Article URL to fetch and summarize"),
    text: Optional[str] = Query(default=None, description="Direct text to summarize"),
    provider: str = Query(default="auto", description="LLM provider: auto, ollama, claude")
) -> Dict[str, Any]:
    """
    Summarize an article using AI/LLM.
    
    Supports three input modes:
    1. article_id: Summarize existing article from database
    2. url: Fetch and summarize article from URL
    3. text: Summarize provided text directly
    
    Args:
        article_id: ID of article in database
        url: URL to fetch and summarize
        text: Direct text to summarize
        provider: LLM provider to use (auto, ollama, claude)
        
    Returns:
        Summarization result with summary, keywords, and metadata
    """
    from llm import ArticleSummarizer, LLMProviderType
    from ingestion.content_parser import ContentParser
    import sqlite3
    from pathlib import Path
    
    try:
        # Validate input - exactly one input method required
        input_count = sum(x is not None for x in [article_id, url, text])
        if input_count != 1:
            raise HTTPException(
                status_code=400, 
                detail="Provide exactly one of: article_id, url, or text"
            )
        
        # Initialize summarizer
        summarizer = ArticleSummarizer()
        
        # Validate provider
        try:
            provider_enum = LLMProviderType(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {provider}. Use: auto, ollama, claude"
            )
        
        article_text = ""
        article_title = None
        source_info = {}
        
        # Get article content based on input method
        if article_id:
            # Fetch from database
            db_path = Path("./data/articles.db")
            if not db_path.exists():
                raise HTTPException(status_code=404, detail="Article database not found")
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("""
                    SELECT title, content, source, url, published_date 
                    FROM articles 
                    WHERE id = ?
                """, (article_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
                
                article_title, article_text, source, url, published_date = row
                source_info = {
                    "source": "database",
                    "article_id": article_id,
                    "original_source": source,
                    "url": url,
                    "published_date": published_date
                }
        
        elif url:
            # Fetch and parse from URL
            logger.info(f"Fetching article from URL: {url}")
            parser = ContentParser()
            parsed_content = await parser.parse_url(url)
            
            if not parsed_content or not parsed_content.get("content"):
                raise HTTPException(
                    status_code=400, 
                    detail="Could not extract readable content from URL"
                )
            
            article_text = parsed_content["content"]
            article_title = parsed_content.get("title")
            source_info = {
                "source": "url",
                "url": url,
                "extraction_method": parsed_content.get("extraction_method")
            }
        
        else:
            # Use provided text directly
            article_text = text
            source_info = {"source": "direct_text"}
        
        # Validate content length
        if not article_text or len(article_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Article text is too short to summarize (minimum 50 characters)"
            )
        
        # Perform summarization
        logger.info(f"Summarizing article using provider: {provider}")
        result = await summarizer.summarize_article(
            article_text=article_text,
            title=article_title,
            provider=provider_enum
        )
        
        # Add source information to result
        result.update(source_info)
        
        logger.info(f"Successfully summarized article (length: {len(article_text)} -> {len(result['summary'])})")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.get("/summarize/status", tags=["AI"])
async def get_summarization_status() -> Dict[str, Any]:
    """
    Get status of available LLM providers for summarization.
    
    Returns:
        Provider status and availability information
    """
    try:
        from llm import ArticleSummarizer
        
        summarizer = ArticleSummarizer()
        status = await summarizer.get_provider_status()
        
        return {
            "message": "Summarization service status",
            **status
        }
        
    except Exception as e:
        logger.error(f"Error checking summarization status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check service status")


@router.get("/search", tags=["Search"])
async def search_articles() -> Dict[str, str]:
    """Search articles using semantic search (placeholder)."""
    return {"message": "Search endpoint - coming soon"}


@router.post("/embeddings/generate", tags=["Embeddings"])
async def generate_embeddings(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum articles to process"),
    force: bool = Query(default=False, description="Force regeneration of existing embeddings")
) -> Dict[str, Any]:
    """
    Generate embeddings for articles that don't have them yet.
    
    This endpoint processes articles in the database and generates vector embeddings
    for semantic search functionality. Only processes articles with content.
    
    Args:
        limit: Maximum number of articles to process
        force: Whether to regenerate embeddings for articles that already have them
        
    Returns:
        Processing summary with statistics
    """
    try:
        import sys
        import os
        
        # Add current directory to path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)
        
        from manage_embeddings import ArticleEmbeddingManager
        
        logger.info(f"Embedding generation requested (limit: {limit}, force: {force})")
        
        manager = ArticleEmbeddingManager()
        
        try:
            # Set up database schema
            await manager.setup_database()
            
            # Get initial statistics
            initial_stats = await manager.get_embedding_statistics()
            
            if not force and initial_stats["pending_articles"] == 0:
                return {
                    "message": "All articles already have embeddings",
                    "stats": initial_stats,
                    "processed": 0
                }
            
            # Get articles to process
            if force:
                # Get all articles if forcing regeneration
                import sqlite3
                from pathlib import Path
                
                db_path = Path("./data/articles.db")
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT id, title, content, summary, source, url, published_date
                        FROM articles 
                        WHERE content IS NOT NULL
                        ORDER BY published_date DESC
                        LIMIT ?
                    """, (limit,))
                    
                    rows = cursor.fetchall()
                    articles = [dict(row) for row in rows]
            else:
                # Get only articles without embeddings
                articles = await manager.get_articles_without_embeddings(limit=limit)
            
            if not articles:
                return {
                    "message": "No articles found to process",
                    "stats": initial_stats,
                    "processed": 0
                }
            
            # Process articles
            processed_count = await manager.generate_embeddings_for_articles(
                articles, 
                batch_size=10
            )
            
            # Get final statistics
            final_stats = await manager.get_embedding_statistics()
            
            return {
                "message": f"Successfully processed {processed_count} articles",
                "initial_stats": initial_stats,
                "final_stats": final_stats,
                "processed": processed_count,
                "total_requested": len(articles),
                "success_rate": round(processed_count / len(articles) * 100, 1) if articles else 0
            }
            
        finally:
            await manager.cleanup()
            
    except ImportError as e:
        logger.error(f"Embedding dependencies not available: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail="Embedding functionality requires sentence-transformers. Install with: pip install sentence-transformers"
        )
    except Exception as e:
        logger.error(f"Error during embedding generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.get("/embeddings/status", tags=["Embeddings"])
async def get_embedding_status() -> Dict[str, Any]:
    """
    Get status of article embeddings in the database.
    
    Returns:
        Embedding statistics and model information
    """
    try:
        import sys
        import os
        
        # Add current directory to path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)
        
        from manage_embeddings import ArticleEmbeddingManager
        from vectorstore.embeddings import EmbeddingGenerator
        
        # Get database statistics
        manager = ArticleEmbeddingManager()
        try:
            stats = await manager.get_embedding_statistics()
        finally:
            await manager.cleanup()
        
        # Get model information
        generator = EmbeddingGenerator()
        model_info = generator.get_model_info()
        
        return {
            "message": "Embedding status retrieved successfully",
            "database_stats": stats,
            "model_info": model_info,
            "embedding_ready": stats["embedded_articles"] > 0
        }
        
    except ImportError:
        return {
            "message": "Embedding functionality not available",
            "database_stats": {
                "total_articles": 0,
                "embedded_articles": 0,
                "pending_articles": 0,
                "completion_rate": 0,
                "model_stats": {}
            },
            "model_info": {
                "available": False,
                "error": "sentence-transformers not installed"
            },
            "embedding_ready": False
        }
    except Exception as e:
        logger.error(f"Error checking embedding status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check embedding status: {str(e)}")
