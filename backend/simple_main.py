"""
Simplified AI Tech News Assistant Backend - Quick Start Version
==============================================================

A lightweight version of the backend that runs without heavy ML dependencies.
Perfect for local development and testing the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn
from typing import List, Dict, Any
import random

# Create FastAPI app
app = FastAPI(
    title="AI Tech News Assistant",
    description="Simplified backend for local development",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample news data
SAMPLE_ARTICLES = [
    {
        "id": "1",
        "title": "Revolutionary AI Model Achieves Breakthrough in Natural Language Understanding",
        "summary": "Researchers have developed a new AI model that demonstrates unprecedented capabilities in understanding context and nuance in human language, potentially revolutionizing chatbots and virtual assistants.",
        "url": "https://example.com/ai-breakthrough",
        "source": "TechCrunch",
        "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
        "category": "Artificial Intelligence",
        "reading_time": 4,
        "sentiment": "positive"
    },
    {
        "id": "2", 
        "title": "Quantum Computing Startup Secures $100M Series B Funding",
        "summary": "A promising quantum computing startup has raised $100 million in Series B funding to accelerate development of practical quantum computers for enterprise applications.",
        "url": "https://example.com/quantum-funding",
        "source": "VentureBeat",
        "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
        "category": "Quantum Computing",
        "reading_time": 3,
        "sentiment": "positive"
    },
    {
        "id": "3",
        "title": "New Cybersecurity Framework Addresses AI-Generated Threats",
        "summary": "Security experts have released a comprehensive framework for defending against sophisticated AI-generated cyber attacks, including deepfake social engineering and automated vulnerability exploitation.",
        "url": "https://example.com/cybersecurity-ai",
        "source": "Wired",
        "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
        "category": "Cybersecurity", 
        "reading_time": 6,
        "sentiment": "neutral"
    },
    {
        "id": "4",
        "title": "Apple Announces New Neural Engine in M4 Chip Architecture",
        "summary": "Apple's latest M4 chip features a dramatically improved Neural Engine with 40% better performance for machine learning tasks, setting new standards for AI processing in consumer devices.",
        "url": "https://example.com/apple-m4-neural",
        "source": "The Verge",
        "published_at": (datetime.now() - timedelta(hours=12)).isoformat(),
        "category": "Hardware",
        "reading_time": 5,
        "sentiment": "positive"
    },
    {
        "id": "5",
        "title": "Open Source AI Model Rivals GPT-4 Performance",
        "summary": "A new open-source language model has achieved performance metrics comparable to GPT-4 while being completely transparent and freely available for researchers and developers.",
        "url": "https://example.com/open-source-ai",
        "source": "MIT Technology Review",
        "published_at": (datetime.now() - timedelta(hours=18)).isoformat(),
        "category": "Open Source",
        "reading_time": 7,
        "sentiment": "positive"
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Tech News Assistant API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/ping")
async def ping():
    """Ping endpoint"""
    return {
        "message": "pong",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/news/stats")
async def get_news_stats():
    """Get news statistics"""
    categories = {}
    for article in SAMPLE_ARTICLES:
        category = article["category"]
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "total_articles": len(SAMPLE_ARTICLES),
        "categories": categories,
        "last_updated": datetime.now().isoformat(),
        "sources": len(set(article["source"] for article in SAMPLE_ARTICLES))
    }

@app.get("/api/v1/news/articles")
async def get_articles(limit: int = 10, category: str = None, search: str = None):
    """Get news articles with optional filtering"""
    articles = SAMPLE_ARTICLES.copy()
    
    # Filter by category if provided
    if category and category.lower() != "all":
        articles = [a for a in articles if a["category"].lower() == category.lower()]
    
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
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/news/articles/{article_id}")
async def get_article(article_id: str):
    """Get a specific article by ID"""
    article = next((a for a in SAMPLE_ARTICLES if a["id"] == article_id), None)
    if not article:
        return {"error": "Article not found"}, 404
    
    return article

@app.get("/api/v1/news/categories")
async def get_categories():
    """Get available categories"""
    categories = list(set(article["category"] for article in SAMPLE_ARTICLES))
    return {
        "categories": sorted(categories),
        "count": len(categories)
    }

@app.get("/api/v1/news/sources") 
async def get_sources():
    """Get available sources"""
    sources = {}
    for article in SAMPLE_ARTICLES:
        source = article["source"]
        sources[source] = sources.get(source, 0) + 1
    
    return {
        "sources": sources,
        "count": len(sources)
    }

@app.post("/api/v1/news/search")
async def search_articles(query: Dict[str, Any]):
    """Advanced search for articles"""
    search_term = query.get("query", "")
    category = query.get("category")
    limit = query.get("limit", 10)
    
    return await get_articles(limit=limit, category=category, search=search_term)

if __name__ == "__main__":
    print("🚀 Starting AI Tech News Assistant - Simple Backend")
    print("📊 Sample data loaded with 5 articles")
    print("🌐 Frontend proxy: http://localhost:3000")
    print("📚 API docs: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
