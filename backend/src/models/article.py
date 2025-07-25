"""
Article Data Models
==================

Pydantic models for article data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ArticleBase(BaseModel):
    """Base article model with common fields."""
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, description="Full article content")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    source: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., description="Original article URL")
    published_date: Optional[datetime] = Field(None, description="Publication date")


class ArticleCreate(ArticleBase):
    """Model for creating new articles."""
    author: Optional[str] = Field(None, description="Article author")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    categories: Optional[List[str]] = Field(None, description="Article categories")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ArticleUpdate(BaseModel):
    """Model for updating existing articles."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None


class Article(ArticleBase):
    """Complete article model with all fields."""
    id: int = Field(..., description="Unique article identifier")
    author: Optional[str] = Field(None, description="Article author")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    categories: Optional[List[str]] = Field(None, description="Article categories")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    embedding_model: Optional[str] = Field(None, description="Model used for embedding")
    embedding_dim: Optional[int] = Field(None, description="Embedding dimension")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_archived: Optional[bool] = Field(False, description="Whether article is archived")
    view_count: Optional[int] = Field(0, description="Number of times article has been viewed")
    embedding_generated: Optional[bool] = Field(False, description="Whether embedding has been generated")
    
    class Config:
        from_attributes = True


class ArticleSummary(BaseModel):
    """Model for article summary information."""
    id: int
    title: str
    summary: Optional[str]
    source: str
    published_date: Optional[datetime]
    url: Optional[str]


class ArticleStats(BaseModel):
    """Model for article statistics."""
    total_articles: int = Field(0, description="Total number of articles")
    articles_with_summaries: int = Field(0, description="Articles with AI summaries")
    articles_with_embeddings: int = Field(0, description="Articles with embeddings")
    sources: Dict[str, int] = Field(default_factory=dict, description="Articles per source")
    date_range: Optional[Dict[str, Optional[datetime]]] = Field(None, description="Date range of articles")


class ArticleSearchRequest(BaseModel):
    """Model for article search requests."""
    query: Optional[str] = Field(None, max_length=500)
    limit: int = Field(20, ge=1, le=100)
    source: Optional[str] = None
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)


class ArticleSearchResult(BaseModel):
    """Model for article search results."""
    article: Article
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    matching_snippets: List[str] = Field(default_factory=list)


class SummarizationRequest(BaseModel):
    """Model for article summarization requests."""
    content: str = Field(..., min_length=1, description="Content to summarize")
    title: Optional[str] = Field(None, description="Article title")
    max_length: int = Field(200, ge=50, le=1000, description="Maximum summary length in words")
    style: str = Field("concise", pattern="^(concise|detailed|bullet_points)$", description="Summary style")
    focus_keywords: Optional[List[str]] = Field(None, description="Keywords to focus on in summary")
