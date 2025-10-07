"""
Search Models
=============

Pydantic models for semantic search API requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text",
        example="latest developments in AI and machine learning"
    )
    
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0-1)"
    )
    
    sources: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific news sources",
        example=["hackernews", "techcrunch"]
    )
    
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by article categories",
        example=["AI", "Machine Learning"]
    )
    
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter articles published after this date"
    )
    
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter articles published before this date"
    )
    
    use_reranking: bool = Field(
        default=True,
        description="Apply reranking to improve result quality"
    )
    
    include_summary: bool = Field(
        default=True,
        description="Include AI-generated summary in results"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and clean query string."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "latest AI breakthroughs in natural language processing",
                "limit": 10,
                "min_score": 0.5,
                "sources": ["hackernews", "techcrunch"],
                "use_reranking": True,
                "include_summary": True
            }
        }


class SearchResultItem(BaseModel):
    """Single search result item."""
    
    id: str = Field(..., description="Article unique identifier")
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication date")
    
    content: Optional[str] = Field(
        None,
        description="Article content excerpt"
    )
    
    summary: Optional[str] = Field(
        None,
        description="AI-generated summary"
    )
    
    categories: List[str] = Field(
        default_factory=list,
        description="Article categories/tags"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted keywords"
    )
    
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score with query (0-1)"
    )
    
    relevance_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Reranked relevance score (0-1)"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "title": "GPT-4 Shows Remarkable Performance",
                "url": "https://example.com/article",
                "source": "techcrunch",
                "published_at": "2025-10-06T12:00:00Z",
                "summary": "Latest GPT-4 demonstrates...",
                "categories": ["AI", "Machine Learning"],
                "keywords": ["GPT-4", "LLM", "OpenAI"],
                "similarity_score": 0.85,
                "relevance_score": 0.92
            }
        }


class SearchResponse(BaseModel):
    """Response model for semantic search."""
    
    query: str = Field(..., description="Original search query")
    
    results: List[SearchResultItem] = Field(
        default_factory=list,
        description="Ranked search results"
    )
    
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of results found"
    )
    
    execution_time_ms: float = Field(
        ...,
        ge=0,
        description="Query execution time in milliseconds"
    )
    
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters that were applied"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata about the search"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "AI breakthroughs",
                "results": [],
                "total_results": 15,
                "execution_time_ms": 142.5,
                "filters_applied": {
                    "sources": ["hackernews"],
                    "min_score": 0.5
                },
                "metadata": {
                    "embedding_model": "all-MiniLM-L6-v2",
                    "reranking_applied": True
                }
            }
        }


class SearchHealthResponse(BaseModel):
    """Health check response for search service."""
    
    status: str = Field(..., description="Service status")
    embeddings_available: bool = Field(..., description="Whether embeddings are available")
    total_indexed_articles: int = Field(..., ge=0, description="Total articles with embeddings")
    last_indexed: Optional[datetime] = Field(None, description="Last indexing timestamp")
    vector_dimensions: Optional[int] = Field(None, description="Embedding vector dimensions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "embeddings_available": True,
                "total_indexed_articles": 1523,
                "last_indexed": "2025-10-07T18:00:00Z",
                "vector_dimensions": 384
            }
        }
