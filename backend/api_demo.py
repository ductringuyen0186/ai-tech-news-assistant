"""
AI/ML Demo API Endpoints
========================

FastAPI endpoints specifically for demonstrating AI/ML features.
These endpoints showcase the core capabilities for demo purposes.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

from demo_ai_ml import AIMLDemo

router = APIRouter(prefix="/demo", tags=["AI/ML Demo"])


class DemoRequest(BaseModel):
    """Request model for demo operations."""
    step: str = Field(..., description="Demo step to run")
    sources: Optional[List[str]] = Field(default=None, description="News sources to use")
    query: Optional[str] = Field(default=None, description="Search query for semantic search")


class DemoResponse(BaseModel):
    """Response model for demo operations."""
    success: bool
    step: str
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: float


class DemoStatus(BaseModel):
    """Demo status model."""
    status: str
    current_step: Optional[str] = None
    progress: float = 0.0
    results: Dict[str, Any] = Field(default_factory=dict)


# Global demo instance and status
demo_instance = None
demo_status = DemoStatus(status="ready")


@router.get("/status", response_model=DemoStatus)
async def get_demo_status():
    """Get current demo status."""
    return demo_status


@router.post("/run-full", response_model=DemoResponse)
async def run_full_demo(background_tasks: BackgroundTasks):
    """
    Run the complete AI/ML demo pipeline.
    This showcases all features from ingestion to semantic search.
    """
    global demo_status
    
    if demo_status.status == "running":
        raise HTTPException(status_code=409, detail="Demo is already running")
    
    # Start demo in background
    background_tasks.add_task(execute_full_demo)
    
    demo_status.status = "running"
    demo_status.current_step = "initializing"
    demo_status.progress = 0.0
    
    return DemoResponse(
        success=True,
        step="full_demo",
        message="Full AI/ML demo started in background",
        processing_time=0.0
    )


@router.post("/run-step", response_model=DemoResponse)
async def run_demo_step(request: DemoRequest):
    """
    Run a specific demo step.
    Available steps: ingestion, summarization, embeddings, search
    """
    start_time = datetime.now()
    
    try:
        global demo_instance
        if not demo_instance:
            demo_instance = AIMLDemo()
        
        result = None
        
        if request.step == "ingestion":
            result = await demo_instance.step_2_news_ingestion()
            message = f"Ingested {len(result)} articles from RSS feeds"
            
        elif request.step == "summarization":
            # Mock articles for demo
            mock_articles = [
                {
                    "title": "AI Breakthrough in Language Models",
                    "content": "Recent developments in artificial intelligence have shown remarkable progress in language understanding and generation capabilities...",
                    "url": "https://example.com/ai-breakthrough"
                },
                {
                    "title": "Startup Raises $50M for Quantum Computing",
                    "content": "A quantum computing startup has secured significant funding to advance their revolutionary quantum processor technology...",
                    "url": "https://example.com/quantum-funding"
                }
            ]
            result = await demo_instance.step_4_ai_summarization(mock_articles)
            message = f"Generated AI summaries for {len(result)} articles"
            
        elif request.step == "embeddings":
            mock_articles = [
                {
                    "title": "Machine Learning Advances",
                    "ai_summary": "Latest developments in ML algorithms show improved efficiency and accuracy across multiple domains.",
                    "url": "https://example.com/ml-advances"
                }
            ]
            result = await demo_instance.step_5_embedding_generation(mock_articles)
            message = f"Generated embeddings for {len(result)} articles"
            
        elif request.step == "search":
            if not request.query:
                raise HTTPException(status_code=400, detail="Query parameter required for search demo")
            
            # Mock search with sample data
            mock_results = [
                {
                    "title": "AI Research Breakthrough",
                    "similarity": 0.95,
                    "summary": "Significant advances in artificial intelligence research..."
                },
                {
                    "title": "Machine Learning Applications",
                    "similarity": 0.87,
                    "summary": "New applications of ML in various industries..."
                }
            ]
            result = mock_results
            message = f"Found {len(result)} articles matching '{request.query}'"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown demo step: {request.step}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DemoResponse(
            success=True,
            step=request.step,
            message=message,
            data={"results": result},
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(
            status_code=500, 
            detail=f"Demo step failed: {str(e)}"
        )


@router.get("/features", response_model=Dict[str, Any])
async def get_demo_features():
    """
    Get information about available AI/ML features.
    This endpoint describes what the demo can showcase.
    """
    return {
        "features": {
            "news_ingestion": {
                "description": "Automated RSS feed scraping from tech news sources",
                "sources": ["HackerNews", "TechCrunch", "The Verge", "Ars Technica"],
                "capabilities": ["RSS parsing", "Content extraction", "Metadata collection"]
            },
            "ai_summarization": {
                "description": "AI-powered article summarization using LLMs",
                "models": ["Ollama (Local)", "Claude (API)", "Extractive (Fallback)"],
                "capabilities": ["Technical summaries", "Key insights extraction", "Custom length control"]
            },
            "semantic_embeddings": {
                "description": "Vector embeddings for semantic search and similarity",
                "models": ["Sentence Transformers", "all-MiniLM-L6-v2", "all-mpnet-base-v2"],
                "capabilities": ["Text-to-vector conversion", "Semantic similarity", "Batch processing"]
            },
            "semantic_search": {
                "description": "Advanced search using vector similarity and hybrid methods",
                "modes": ["Text search", "Semantic search", "Hybrid search"],
                "capabilities": ["Natural language queries", "Similarity scoring", "Relevance ranking"]
            },
            "rag_system": {
                "description": "Retrieval-Augmented Generation for intelligent Q&A",
                "components": ["Vector retrieval", "LLM generation", "Context integration"],
                "capabilities": ["Question answering", "Source attribution", "Contextual responses"]
            }
        },
        "demo_endpoints": {
            "/demo/run-full": "Run complete AI/ML pipeline demo",
            "/demo/run-step": "Run individual demo steps",
            "/demo/status": "Check demo execution status",
            "/demo/features": "Get feature information"
        },
        "tech_stack": {
            "backend": "FastAPI + SQLAlchemy",
            "ai_ml": "Sentence Transformers + LangChain",
            "llm": "Ollama (Local) + Claude (API)",
            "vector_db": "Chroma + SQLite",
            "processing": "AsyncIO + Background Tasks"
        }
    }


@router.post("/test-llm", response_model=DemoResponse)
async def test_llm_connection():
    """Test LLM provider connectivity for demo."""
    start_time = datetime.now()
    
    try:
        global demo_instance
        if not demo_instance:
            demo_instance = AIMLDemo()
        
        # Test Ollama
        ollama_available = await demo_instance.ollama_provider.is_available()
        
        # Test Claude (if configured)
        claude_available = False
        if demo_instance.claude_provider:
            claude_available = await demo_instance.claude_provider.is_available()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return DemoResponse(
            success=True,
            step="llm_test",
            message="LLM connectivity tested",
            data={
                "ollama_available": ollama_available,
                "claude_available": claude_available,
                "recommendations": get_llm_setup_recommendations(ollama_available, claude_available)
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(
            status_code=500,
            detail=f"LLM test failed: {str(e)}"
        )


@router.post("/quick-search", response_model=DemoResponse)
async def quick_semantic_search(
    query: str = Field(..., description="Search query"),
    limit: int = Field(5, ge=1, le=20, description="Number of results")
):
    """Quick semantic search demo with mock data."""
    start_time = datetime.now()
    
    # Mock search results for demo
    mock_results = [
        {
            "id": 1,
            "title": "Advances in Large Language Models",
            "summary": "Recent breakthroughs in LLM architecture and training methods",
            "similarity": 0.94,
            "source": "AI Research Blog",
            "published": "2025-08-16"
        },
        {
            "id": 2,
            "title": "Vector Databases for AI Applications",
            "summary": "How vector databases enable semantic search and RAG systems",
            "similarity": 0.89,
            "source": "Tech Weekly",
            "published": "2025-08-15"
        },
        {
            "id": 3,
            "title": "Embedding Models Comparison Study",
            "summary": "Performance analysis of different embedding models for text similarity",
            "similarity": 0.85,
            "source": "ML Journal",
            "published": "2025-08-14"
        }
    ]
    
    # Filter results based on limit
    filtered_results = mock_results[:limit]
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return DemoResponse(
        success=True,
        step="semantic_search",
        message=f"Found {len(filtered_results)} relevant articles for '{query}'",
        data={
            "query": query,
            "results": filtered_results,
            "total_found": len(mock_results)
        },
        processing_time=processing_time
    )


async def execute_full_demo():
    """Execute the full demo in background."""
    global demo_status, demo_instance
    
    try:
        demo_instance = AIMLDemo()
        demo_status.current_step = "setup"
        demo_status.progress = 10.0
        
        await demo_instance.step_1_setup()
        
        demo_status.current_step = "ingestion"
        demo_status.progress = 25.0
        articles = await demo_instance.step_2_news_ingestion()
        demo_status.results["articles_count"] = len(articles)
        
        demo_status.current_step = "processing"
        demo_status.progress = 40.0
        processed = await demo_instance.step_3_content_processing(articles)
        
        demo_status.current_step = "summarization"
        demo_status.progress = 60.0
        summarized = await demo_instance.step_4_ai_summarization(processed)
        demo_status.results["summaries_count"] = len(summarized)
        
        demo_status.current_step = "embeddings"
        demo_status.progress = 80.0
        embedded = await demo_instance.step_5_embedding_generation(summarized)
        demo_status.results["embeddings_count"] = len(embedded)
        
        demo_status.current_step = "search_demo"
        demo_status.progress = 90.0
        await demo_instance.step_6_semantic_search_demo(embedded)
        
        demo_status.current_step = "rag_demo"
        demo_status.progress = 95.0
        await demo_instance.step_7_rag_query_demo()
        
        demo_status.status = "completed"
        demo_status.progress = 100.0
        demo_status.current_step = "finished"
        
    except Exception as e:
        demo_status.status = "failed"
        demo_status.current_step = f"error: {str(e)}"


def get_llm_setup_recommendations(ollama_available: bool, claude_available: bool) -> List[str]:
    """Get setup recommendations based on LLM availability."""
    recommendations = []
    
    if not ollama_available and not claude_available:
        recommendations.extend([
            "Install Ollama for local LLM inference: https://ollama.ai/download",
            "Pull a model: ollama pull llama2",
            "Or get Claude API key: https://console.anthropic.com/"
        ])
    elif not ollama_available:
        recommendations.append("Consider installing Ollama for local inference")
    elif not claude_available:
        recommendations.append("Consider adding Claude API key for cloud inference")
    else:
        recommendations.append("All LLM providers are available!")
    
    return recommendations
