"""
Data Models
==========
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Import user models
from .user import (
    UserDB, UserPreferenceDB, TechCategory,
    UserCreate, UserLogin, UserUpdate, User,
    UserPreferenceUpdate, UserPreference,
    Token, TokenData,
    user_bookmarks, reading_history
)


class ArticleDB(Base):
    """SQLAlchemy model for articles"""
    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    source_id = Column(String(100), nullable=True, index=True)

    # AI-generated metadata
    categories = Column(JSON, default=list)  # List of TechCategory values
    keywords = Column(JSON, default=list)  # Extracted keywords
    ai_summary = Column(Text, nullable=True)  # AI-generated summary
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Analytics
    view_count = Column(Integer, default=0)
    summary_count = Column(Integer, default=0)

    # Quality scores
    relevance_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source={self.source})>"


# Pydantic models for API
class ArticleBase(BaseModel):
    """Base article model"""
    title: str
    content: str
    url: HttpUrl
    published_at: datetime
    source: str
    source_id: Optional[str] = None
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class ArticleCreate(ArticleBase):
    """Article creation model"""
    pass


class ArticleUpdate(BaseModel):
    """Article update model"""
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[HttpUrl] = None
    published_at: Optional[datetime] = None


class Article(ArticleBase):
    """Full article model with metadata"""
    id: str
    categories: List[str] = []
    keywords: List[str] = []
    ai_summary: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    view_count: int = 0
    summary_count: int = 0
    relevance_score: float = 0.0
    engagement_score: float = 0.0

    class Config:
        from_attributes = True


class ArticleList(BaseModel):
    """Article list response"""
    articles: List[Article]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    limit: Optional[int] = 10
    offset: Optional[int] = 0
    source_filter: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()
    
    @validator('limit')
    def limit_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Limit must be positive')
        return min(v or 10, 100)  # Max 100 results


class SearchResult(BaseModel):
    """Search result with relevance score"""
    article: Article
    relevance_score: float
    highlight_snippet: Optional[str] = None


class SearchResponse(BaseModel):
    """Search response model"""
    results: List[SearchResult]
    total: int
    query: str
    took_ms: int


class SummarizeRequest(BaseModel):
    """Summarization request"""
    text: str
    max_length: Optional[int] = 150
    use_ai: Optional[bool] = True
    
    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text to summarize cannot be empty')
        return v.strip()
    
    @validator('max_length')
    def max_length_must_be_reasonable(cls, v):
        if v is not None and (v < 50 or v > 500):
            raise ValueError('Max length must be between 50 and 500 characters')
        return v


class SummaryResponse(BaseModel):
    """Summary response model"""
    summary: str
    method: str
    original_length: int
    summary_length: int
    processing_time_ms: int
    confidence_score: Optional[float] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    components: dict
    uptime_seconds: int


class NewsSource(BaseModel):
    """News source configuration"""
    name: str
    enabled: bool
    last_fetch: Optional[datetime] = None
    article_count: int = 0
    success_rate: float = 0.0
    avg_response_time_ms: int = 0


class SystemStats(BaseModel):
    """System statistics"""
    total_articles: int
    sources: List[NewsSource]
    cache_size: int
    last_fetch: Optional[datetime] = None
    uptime_seconds: int
    requests_per_hour: int