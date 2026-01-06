"""
Multi-Agent API Routes
======================

API endpoints for LangChain multi-agent orchestration.

Features:
- Sequential agent workflows (research → analyze → summarize)
- Conversational Q&A with memory
- Article ingestion to vector store
- Agent health monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from agents.langchain_agent import get_agent_orchestrator
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/agents", tags=["Multi-Agent System"])


# Request/Response Models
class ResearchRequest(BaseModel):
    """Request for multi-agent research workflow."""
    query: str = Field(..., description="Research query or topic")
    top_k: int = Field(5, ge=1, le=20, description="Number of articles to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest developments in AI language models?",
                "top_k": 5
            }
        }


class QARequest(BaseModel):
    """Request for conversational Q&A."""
    question: str = Field(..., description="User question")
    chat_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How is AI being used in healthcare?",
                "chat_history": []
            }
        }


class IngestArticlesRequest(BaseModel):
    """Request to ingest articles into vector store."""
    articles: List[Dict[str, Any]] = Field(..., description="Articles to ingest")
    
    class Config:
        json_schema_extra = {
            "example": {
                "articles": [
                    {
                        "id": "123",
                        "title": "AI Breakthrough",
                        "content": "Scientists have developed...",
                        "source": "TechCrunch",
                        "url": "https://example.com/article"
                    }
                ]
            }
        }


@router.post("/research")
async def multi_agent_research(request: ResearchRequest) -> Dict[str, Any]:
    """
    Execute multi-agent research workflow.
    
    Agents executed in sequence:
    1. **Research Agent** - Plans search strategy
    2. **Retrieval** - Finds relevant articles from vector store
    3. **Analysis Agent** - Identifies trends and patterns
    4. **Summarization Agent** - Creates comprehensive summary
    
    This is a demonstration of sequential agent orchestration with LangChain.
    
    **Cost**: FREE with Groq API (or use free tier of other LLMs)
    
    Returns:
        - research_plan: Research strategy from agent 1
        - articles_found: Number of articles retrieved
        - articles: List of relevant articles with snippets
        - analysis: Trend analysis from agent 2
        - summary: Final summary from agent 3
        - agents_executed: List of agents that ran
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        result = await orchestrator.research_and_analyze(
            query=request.query,
            top_k=request.top_k
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            "success": True,
            "message": "Multi-agent research completed",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Multi-agent research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qa")
async def conversational_qa(request: QARequest) -> Dict[str, Any]:
    """
    Conversational Q&A with context and memory.
    
    Uses LangChain's RetrievalQA with:
    - Vector store retrieval (finds relevant articles)
    - LLM generation (Groq for fast responses)
    - Source attribution (shows which articles were used)
    - Conversation memory (maintains context)
    
    **Cost**: FREE with Groq API (or ~$0.0001 per question with paid APIs)
    
    Returns:
        - question: User's question
        - answer: AI-generated answer
        - sources: Articles used to answer (with URLs)
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        result = await orchestrator.conversational_qa(
            question=request.question,
            chat_history=request.chat_history
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            "success": True,
            "message": "Question answered",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Conversational QA failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_articles(
    request: IngestArticlesRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Ingest articles into vector store for retrieval.
    
    This endpoint:
    1. Takes article data (title, content, metadata)
    2. Generates embeddings using HuggingFace models (FREE)
    3. Stores in ChromaDB (FREE, local storage)
    4. Makes articles searchable for agents
    
    **Cost**: 100% FREE (local processing, no API calls)
    
    Returns:
        - documents_added: Number of articles ingested
        - total_documents: Total articles in vector store
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        # Add ingestion as background task for large batches
        result = await orchestrator.add_articles_to_vectorstore(
            articles=request.articles
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        return {
            "success": True,
            "message": f"Ingested {result['documents_added']} articles",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Article ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_health() -> Dict[str, Any]:
    """
    Check health of multi-agent system.
    
    Returns:
        - status: Overall system health
        - components: Status of LLM, vector store, embeddings
        - total_documents: Number of articles in vector store
    """
    try:
        orchestrator = await get_agent_orchestrator()
        
        # Check vector store
        vectorstore_status = "healthy"
        total_docs = 0
        try:
            if orchestrator.vectorstore:
                total_docs = orchestrator.vectorstore._collection.count()
        except Exception as e:
            vectorstore_status = f"degraded: {str(e)}"
        
        # Check LLM
        llm_status = "healthy" if orchestrator.llm else "unavailable"
        
        # Check embeddings
        embeddings_status = "healthy" if orchestrator.embeddings else "unavailable"
        
        overall_status = "healthy"
        if "degraded" in vectorstore_status or llm_status != "healthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "components": {
                "llm": llm_status,
                "vectorstore": vectorstore_status,
                "embeddings": embeddings_status
            },
            "total_documents": total_docs,
            "model": orchestrator.model_name
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/info")
async def agent_info() -> Dict[str, Any]:
    """
    Get information about the multi-agent system.
    
    Returns:
        - name: System name
        - version: Version
        - features: Available features
        - costs: Cost information
        - models: Models being used
    """
    return {
        "name": "LangChain Multi-Agent System",
        "version": "1.0.0",
        "description": "Sequential agent orchestration for tech news analysis",
        "features": [
            "Multi-agent research workflows",
            "Conversational Q&A with memory",
            "Vector search with ChromaDB",
            "HuggingFace embeddings",
            "Source attribution",
            "Background processing"
        ],
        "costs": {
            "embeddings": "FREE (HuggingFace local models)",
            "vector_store": "FREE (ChromaDB local storage)",
            "llm_groq": "FREE tier available (100K tokens/day)",
            "total_monthly_cost": "$0-5 depending on LLM usage"
        },
        "models": {
            "embeddings": "all-MiniLM-L6-v2 (HuggingFace)",
            "llm": "llama-3.3-70b-versatile (Groq)",
            "vector_db": "ChromaDB"
        },
        "agents": [
            {
                "name": "Research Agent",
                "purpose": "Plans search strategy and identifies keywords"
            },
            {
                "name": "Analysis Agent",
                "purpose": "Analyzes trends and patterns in articles"
            },
            {
                "name": "Summarization Agent",
                "purpose": "Creates comprehensive summaries"
            },
            {
                "name": "QA Agent",
                "purpose": "Answers questions with source attribution"
            }
        ],
        "endpoints": [
            "POST /api/agents/research - Multi-agent research workflow",
            "POST /api/agents/qa - Conversational Q&A",
            "POST /api/agents/ingest - Ingest articles to vector store",
            "GET /api/agents/health - System health check",
            "GET /api/agents/info - This endpoint"
        ]
    }
