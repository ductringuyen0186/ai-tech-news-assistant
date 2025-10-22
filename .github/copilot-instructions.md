# GitHub Copilot Instructions for AI Tech News Assistant

> **Project Context**: Advanced AI-powered tech news aggregation platform with RAG (Retrieval-Augmented Generation), vector search, and multi-LLM support.

## 🎯 Project Overview

This is a **full-stack AI/ML application** with:
- **Backend**: FastAPI (Python 3.11+) with SQLAlchemy, async operations, RAG pipeline, and vector embeddings
- **Frontend**: React 18 + TypeScript + Vite with shadcn/ui and Tailwind CSS (single-page app, no routing)
- **AI/ML**: Multi-LLM support (Ollama, OpenAI, Anthropic), Sentence Transformers embeddings, Chroma vector DB
- **Architecture**: Clean Architecture, Repository Pattern, RAG pipeline, microservices-ready
- **Focus**: Intelligent news aggregation, semantic search, AI summarization, personalized recommendations
- **Authentication**: None currently (using localStorage for preferences, ready for future auth integration)

---

## ⚡ Communication Guidelines

### **DO:**
- ✅ **Make changes directly** - Edit files immediately, don't ask for permission
- ✅ **Be concise** - Give brief summaries of changes (2-3 sentences max)
- ✅ **Use bullet points** - List changes clearly and directly
- ✅ **Commit and push** - Complete the full workflow without asking
- ✅ **Show results** - Demonstrate what was fixed/added with examples

### **DON'T:**
- ❌ **Create documentation/markdown files automatically** - No PROGRESS.md, CHANGES.md, RENDER_DEPLOYMENT.md, FRONTEND_SETUP.md, etc.
  - Exception: If documentation is absolutely necessary, show it in code block for user review FIRST
  - Let user decide whether to keep, modify, or discard before committing
  - Never auto-commit markdown files without explicit user approval
- ❌ **Write lengthy explanations** - Keep responses short and actionable
- ❌ **Add unnecessary comments** - Only comment complex logic or non-obvious code
- ❌ **Ask for confirmation** - Just do it (unless destructive changes)
- ❌ **Repeat context** - Don't restate what the user already knows

### **Response Format:**
```
✅ Fixed [issue] by [action]

Changes:
- file1.py: updated X to Y
- file2.ts: added Z function

Test: [quick validation result]
```

**Complex workflows only**: If the change involves 5+ files or architectural decisions, provide a brief overview. Otherwise, just make the changes and summarize.

### **Documentation & Markdown Files Policy:**

⚠️ **STRICT RULE**: Do NOT auto-generate and commit markdown files without explicit user approval.

**Files NEVER to auto-create:**
- ❌ `ROOT_FILE_CLEANUP.md` - Cleanup/analysis documents
- ❌ `PROGRESS_REPORT.md` - Progress tracking (user manages this)
- ❌ `CHANGES.md` - Change summaries
- ❌ `DEPLOYMENT_GUIDE.md` - Deployment documentation
- ❌ `FRONTEND_SETUP.md` - Setup guides
- ❌ `TESTING_RESULTS.md` - Test reports
- ❌ `REFACTORING_COMPLETE.md` - Refactoring summaries
- ❌ Any other temporary `.md` files

**Workflow for Documentation:**
1. **NEVER create** temporary markdown files (cleanup docs, progress files, analysis docs, etc.)
2. **ONLY update** README.md if absolutely necessary for user benefit (requires explicit request)
3. **If documentation needed**, display content in a code block for user review FIRST
4. **Wait for explicit approval** before committing any `.md` files
5. **Let user decide**: Keep, modify, discard, or update README instead

**Exception cases** (require explicit user request):
- README updates (code changes need to be documented)
- API documentation (auto-generated from code if available)
- Inline code comments (in actual source files, not separate docs)

**Why?** Auto-generated docs clutter the repo, cause merge conflicts, and create maintenance burden. User can write documentation at their own pace. All important information should go in README.md or inline code comments.

---

## 📐 Architecture & Design Principles

### Core Principles
1. **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
2. **Separation of Concerns**: Clear boundaries between layers (API, Service, Repository, Models)
3. **Dependency Injection**: Use FastAPI's dependency injection system extensively
4. **Async-First**: All I/O operations must be async (database, HTTP, file operations)
5. **Type Safety**: Full type hints in Python, strict TypeScript in frontend
6. **Error Handling**: Comprehensive error handling with proper logging and user feedback
7. **Security First**: Input validation, sanitization, authentication, CORS configuration
8. **Performance**: Caching, connection pooling, lazy loading, pagination

---

## 🔧 Backend Development (FastAPI)

### Backend Root Directory Organization

**✅ What belongs at `backend/` root level:**
- `main.py` - FastAPI application entry point (REQUIRED)
- `conftest.py` - pytest configuration for tests (REQUIRED)
- Configuration files: `alembic.ini`, `pytest.ini` (tool-specific, must be at root)
- Database files: `news_assistant.db` (local SQLite, should be in `.gitignore`)
- Lock/dependency files: `requirements.txt`, `pyproject.toml`

**🔧 What belongs in `backend/scripts/`:**
- `validate_config.py` - Configuration validation tool
- `manage_embeddings.py` - Embeddings management utility
- `run_tests.py` - Test runner script
- `create_article_repo.py` - Repository setup utility
- `test_*.py` files that are manual testing scripts (not pytest tests)
- `setup_refactored.py` - One-time setup scripts
- `setup_python.bat`, `test_api.ps1` - Shell scripts

**❌ What should NOT be at root:**
- Debug/check scripts: `check_*.py`, `debug_*.py`, `force_*.py`
- Temporary test files: `quick_test.py`, `run.py`, `simple_main.py`
- Alternate entry points (production deployments should use `main.py`)

**Cleanup Status:**
- ✅ Deleted 12 debug/check files (27.68 KB of noise)
- ✅ Moved 4 utility scripts to `scripts/` folder
- ✅ Kept only essential files at root: `main.py`, `conftest.py`
- ✅ Result: Clean, organized backend structure

### Project Structure Convention
```
backend/
├── src/                     # Main source code (Clean Architecture)
│   ├── api/                 # API layer
│   │   └── routes/          # API route modules
│   │       ├── health.py    # Health check endpoints
│   │       ├── news.py      # News article endpoints
│   │       ├── search.py    # Search and retrieval endpoints
│   │       ├── summarization.py  # AI summarization endpoints
│   │       └── embeddings.py     # Vector embedding endpoints
│   ├── core/                # Core infrastructure
│   │   ├── config.py        # Settings and configuration (Pydantic)
│   │   ├── exceptions.py    # Custom exception classes
│   │   ├── logging.py       # Structured logging setup
│   │   ├── middleware.py    # FastAPI middleware
│   │   └── retry.py         # Retry logic and resilience
│   ├── database/            # Database layer
│   │   ├── base.py          # SQLAlchemy base
│   │   ├── models.py        # Database models
│   │   ├── session.py       # Session management
│   │   └── init_db.py       # Database initialization
│   ├── models/              # Pydantic models for API
│   │   ├── api.py           # Request/Response models
│   │   ├── article.py       # Article domain models
│   │   ├── embedding.py     # Embedding models
│   │   └── health.py        # Health check models
│   ├── repositories/        # Repository pattern (Data Access)
│   │   ├── article_repository.py      # Article data access
│   │   ├── embedding_repository.py    # Vector storage access
│   │   ├── sqlalchemy_repository.py   # Base SQLAlchemy repo
│   │   └── factory.py                 # Repository factory
│   ├── services/            # Business logic layer
│   │   ├── news_service.py           # News aggregation logic
│   │   ├── embedding_service.py      # Embedding generation
│   │   ├── summarization_service.py  # AI summarization
│   │   └── migration_service.py      # Data migration utilities
│   └── main.py              # FastAPI application entry
├── llm/                     # LLM provider implementations
│   ├── providers.py         # Multi-LLM provider interface
│   │   ├── OllamaProvider   # Local LLM (Ollama)
│   │   ├── ClaudeProvider   # Anthropic Claude API
│   │   └── OpenAIProvider   # OpenAI API (future)
│   └── summarizer.py        # LLM-powered summarization
├── vectorstore/             # Vector database operations
│   ├── embeddings.py        # Sentence Transformers interface
│   ├── chroma_store.py      # ChromaDB implementation (future)
│   └── fallback_deps.py     # Graceful fallbacks
├── rag/                     # RAG pipeline (Retrieval-Augmented Generation)
│   ├── __init__.py          # RAG orchestration
│   ├── chunking.py          # Document chunking strategies
│   ├── retrieval.py         # Semantic search and retrieval
│   └── augmentation.py      # Context augmentation for LLM
├── ingestion/               # Data ingestion pipeline
│   ├── rss_feeds.py         # RSS feed parsing and scraping
│   ├── content_parser.py    # Article content extraction
│   └── pipeline.py          # Ingestion orchestration
├── utils/                   # Shared utilities
│   ├── config.py            # Configuration helpers
│   └── logger.py            # Logging utilities
├── tests/                   # Comprehensive test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── alembic/                 # Database migrations
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── pyproject.toml           # Project configuration
```

### Coding Standards

#### 1. **API Endpoints** (`app/api/`)
```python
"""
Module docstring explaining the purpose
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models import Article, ArticleList, SearchRequest
from ..services.database import db_service
from ..core.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["articles"])


@router.get("/articles", response_model=ArticleList)
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
) -> ArticleList:
    """
    Get paginated articles with optional filtering.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        source: Filter by news source
        category: Filter by tech category
        current_user: Authenticated user from dependency
        background_tasks: For async operations
    
    Returns:
        ArticleList with paginated results
        
    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        # Input validation
        if page < 1 or per_page < 1:
            raise HTTPException(400, "Invalid pagination parameters")
        
        # Business logic in service layer
        articles = await db_service.get_articles_paginated(
            page=page,
            per_page=per_page,
            filters={"source": source, "category": category}
        )
        
        # Background task example
        if background_tasks:
            background_tasks.add_task(log_access, current_user.id, "articles")
        
        return ArticleList(
            articles=articles.items,
            total=articles.total,
            page=page,
            per_page=per_page
        )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error fetching articles: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

**Key Points**:
- ✅ Use `async def` for all I/O operations
- ✅ Comprehensive docstrings with Args, Returns, Raises
- ✅ Type hints for all parameters and return types
- ✅ Input validation at API layer
- ✅ Business logic delegated to service layer
- ✅ Structured error handling with appropriate HTTP status codes
- ✅ Logging for debugging and monitoring
- ✅ Use FastAPI's dependency injection (Depends)
- ✅ Query parameters with validation and documentation
- ✅ Background tasks for non-blocking operations

#### 2. **Service Layer** (`app/services/`)
```python
"""
Database Service
===============
Handles all database operations with connection pooling and error handling.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import create_engine, select, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from contextlib import contextmanager

from ..core.config import settings
from ..models import Base, ArticleDB, Article

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Production database service with connection pooling.
    
    Features:
    - Connection pooling for performance
    - Automatic retry logic
    - Comprehensive error handling
    - Transaction management
    """
    
    def __init__(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._create_tables()
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Yields:
            Session: SQLAlchemy database session
            
        Example:
            with db_service.get_session() as session:
                article = session.query(ArticleDB).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def create_article(self, article_data: dict) -> Optional[Article]:
        """
        Create new article with duplicate detection.
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            Created Article or None if duplicate
            
        Raises:
            SQLAlchemyError: For database errors
        """
        try:
            with self.get_session() as session:
                # Generate unique ID
                article_id = self._generate_article_id(article_data["url"])
                
                # Check for duplicates
                existing = session.query(ArticleDB).filter(
                    ArticleDB.id == article_id
                ).first()
                
                if existing:
                    logger.debug(f"Article already exists: {article_id}")
                    return self._to_pydantic(existing)
                
                # Create new article
                db_article = ArticleDB(
                    id=article_id,
                    **article_data
                )
                
                session.add(db_article)
                session.flush()
                
                logger.info(f"Created article: {article_id}")
                return self._to_pydantic(db_article)
                
        except IntegrityError as e:
            logger.warning(f"Duplicate article: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            raise
```

**Key Points**:
- ✅ Single Responsibility: Each service handles one domain
- ✅ Context managers for resource management
- ✅ Connection pooling for production performance
- ✅ Comprehensive error handling with specific exception types
- ✅ Logging at appropriate levels (debug, info, warning, error)
- ✅ Separation of DB models and Pydantic models
- ✅ Transaction management
- ✅ Retry logic for transient failures

#### 3. **Models** (`app/models/`)
```python
"""
Data Models
==========
SQLAlchemy ORM models and Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field, validator
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# SQLAlchemy Models (Database)
class ArticleDB(Base):
    """
    Database model for articles.
    
    Attributes:
        id: Unique article identifier (SHA256 of URL)
        title: Article title (max 500 chars)
        content: Full article content
        url: Article URL (unique, indexed)
        published_at: Publication timestamp (indexed)
        source: Source identifier (indexed)
        categories: JSON list of tech categories
        ai_summary: AI-generated summary
        created_at: Record creation timestamp
    """
    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    
    # AI-generated fields
    categories = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    ai_summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Pydantic Models (API)
class ArticleBase(BaseModel):
    """Base article schema with validation."""
    
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    url: HttpUrl
    published_at: datetime
    source: str = Field(..., min_length=1, max_length=100)
    
    @validator('title', 'content')
    def strip_whitespace(cls, v):
        """Remove leading/trailing whitespace."""
        return v.strip()
    
    @validator('source')
    def validate_source(cls, v):
        """Validate source is from allowed list."""
        allowed_sources = {'hackernews', 'reddit', 'github', 'techcrunch'}
        if v.lower() not in allowed_sources:
            raise ValueError(f"Source must be one of: {allowed_sources}")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "title": "New AI Breakthrough in Language Models",
                "content": "Researchers have developed...",
                "url": "https://example.com/article",
                "published_at": "2025-10-06T12:00:00Z",
                "source": "techcrunch"
            }
        }


class ArticleCreate(ArticleBase):
    """Schema for creating articles."""
    pass


class Article(ArticleBase):
    """Complete article schema with metadata."""
    
    id: str
    categories: List[str] = []
    keywords: List[str] = []
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Allow ORM mode for SQLAlchemy compatibility."""
        from_attributes = True
```

**Key Points**:
- ✅ Separate SQLAlchemy (DB) and Pydantic (API) models
- ✅ Comprehensive field validation
- ✅ Custom validators for business rules
- ✅ Indexes on frequently queried fields
- ✅ JSON fields for flexible data
- ✅ Timestamps for auditing
- ✅ Example schemas in Config
- ✅ Proper type hints

#### 4. **Configuration** (`app/core/config.py`)
```python
"""
Application Configuration
========================
Environment-based settings using Pydantic Settings.
"""
from typing import List, Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Environment variables take precedence over .env file.
    """
    
    # Application
    APP_NAME: str = "AI Tech News Assistant"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = Field("0.0.0.0", description="Server bind address")
    PORT: int = Field(8000, ge=1, le=65535, description="Server port")
    
    # Database
    DATABASE_URL: str = Field(
        "sqlite:///./news.db",
        description="Database connection string"
    )
    DATABASE_ECHO: bool = Field(False, description="Log SQL queries")
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    
    # API Configuration
    MAX_ARTICLES_PER_REQUEST: int = Field(100, ge=1, le=500)
    REQUEST_TIMEOUT: int = Field(30, ge=1, le=300)
    
    # AI/ML
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
```

**Key Points**:
- ✅ Use Pydantic Settings for type-safe configuration
- ✅ Environment variable support
- ✅ Validation on all settings
- ✅ Secure defaults
- ✅ Custom validators for complex types
- ✅ Comprehensive documentation

#### 5. **LLM Providers** (`llm/providers.py`)
```python
"""
LLM Provider Interface
====================
Multi-provider abstraction for LLM operations.
"""
import httpx
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """Summarize text and return structured response."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLM inference.
    
    Features:
    - Local inference (no API costs)
    - Multiple model support (Llama2, Mistral, etc.)
    - Privacy-friendly (data stays local)
    - Fast inference on GPU
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "llama2",
                 timeout: int = 60):
        """Initialize Ollama provider."""
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def summarize(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Summarize text using Ollama.
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length
            
        Returns:
            Dict with summary and metadata
        """
        try:
            prompt = f"""Summarize the following tech article in {max_length} words or less.
Focus on key technical points, innovations, and implications.

Article:
{text}

Summary:"""
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.9}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "summary": result["response"].strip(),
                    "model": self.model,
                    "provider": "ollama",
                    "success": True
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {"success": False, "error": "API error"}
                
        except Exception as e:
            logger.error(f"Ollama summarization failed: {e}")
            return {"success": False, "error": str(e)}


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize Claude provider."""
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
    
    async def summarize(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """Summarize using Claude API."""
        # Implementation here
        pass
```

**Key Points**:
- ✅ Abstract base class for provider-agnostic code
- ✅ Multiple provider support (Ollama, Claude, OpenAI)
- ✅ Graceful fallbacks and error handling
- ✅ Provider availability checks
- ✅ Configurable timeouts and parameters
- ✅ Structured response format

#### 6. **Vector Store & Embeddings** (`vectorstore/embeddings.py`)
```python
"""
Embedding Generator
==================
High-performance text-to-vector conversion using Sentence Transformers.
"""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import torch
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    from .fallback_deps import FallbackSentenceTransformer as SentenceTransformer

from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Efficient embedding generation for semantic search.
    
    Features:
    - Multiple pre-trained models
    - Batch processing
    - GPU acceleration
    - Async-friendly interface
    - Model caching
    """
    
    DEFAULT_MODELS = [
        "all-MiniLM-L6-v2",      # Fast, 384 dims
        "all-mpnet-base-v2",     # Quality, 768 dims
        "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual
    ]
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize embedding generator."""
        self.model_name = model_name or self.DEFAULT_MODELS[0]
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Embedding generator using device: {self.device}")
    
    async def initialize(self):
        """Load the model asynchronously."""
        if not EMBEDDINGS_AVAILABLE:
            logger.warning("Sentence Transformers not available, using fallback")
            return
        
        try:
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                lambda: SentenceTransformer(self.model_name, device=self.device)
            )
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def generate_embeddings(
        self, 
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings
        """
        if not self.model:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
```

**Key Points**:
- ✅ Async-friendly interface with asyncio
- ✅ GPU acceleration when available
- ✅ Batch processing for efficiency
- ✅ Graceful fallbacks for missing dependencies
- ✅ Multiple model support
- ✅ Error handling and logging

#### 7. **RAG Pipeline** (`rag/__init__.py`)
```python
"""
RAG (Retrieval-Augmented Generation) Pipeline
=============================================
Orchestrates document retrieval and context augmentation for LLM queries.
"""
from typing import List, Dict, Any, Optional

from utils.logger import get_logger
from vectorstore.embeddings import EmbeddingGenerator

logger = get_logger(__name__)


class RAGPipeline:
    """
    RAG pipeline for intelligent document retrieval.
    
    Features:
    - Document chunking and preprocessing
    - Semantic search via embeddings
    - Context ranking and filtering
    - Metadata-based filtering
    - Query augmentation
    """
    
    def __init__(self, embedding_generator: EmbeddingGenerator):
        """Initialize RAG pipeline."""
        self.embedding_generator = embedding_generator
        self.documents = []  # In-memory store (use Chroma in production)
        logger.info("RAG Pipeline initialized")
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]],
        chunk_size: int = 500,
        overlap: int = 50
    ) -> bool:
        """
        Add documents to RAG system with chunking.
        
        Args:
            documents: Documents to add
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            Success status
        """
        try:
            chunked_docs = []
            for doc in documents:
                chunks = self._chunk_document(doc, chunk_size, overlap)
                chunked_docs.extend(chunks)
            
            # Generate embeddings
            texts = [chunk["text"] for chunk in chunked_docs]
            embeddings = await self.embedding_generator.generate_embeddings(texts)
            
            # Store with embeddings
            for chunk, embedding in zip(chunked_docs, embeddings):
                chunk["embedding"] = embedding
                self.documents.append(chunk)
            
            logger.info(f"Added {len(chunked_docs)} document chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters (source, date, etc.)
            
        Returns:
            Ranked list of relevant documents
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embeddings([query])
            
            # Compute similarity scores
            results = []
            for doc in self.documents:
                # Apply filters
                if filters and not self._match_filters(doc, filters):
                    continue
                
                # Compute cosine similarity
                similarity = self._cosine_similarity(
                    query_embedding[0], 
                    doc["embedding"]
                )
                
                results.append({
                    "document": doc,
                    "score": similarity
                })
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _chunk_document(
        self, 
        doc: Dict[str, Any], 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, Any]]:
        """Chunk document with overlap."""
        text = doc.get("content", "")
        chunks = []
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            chunks.append({
                "text": chunk_text,
                "metadata": doc.get("metadata", {}),
                "source_id": doc.get("id")
            })
        
        return chunks
    
    @staticmethod
    def _cosine_similarity(a, b):
        """Compute cosine similarity between vectors."""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

**Key Points**:
- ✅ Document chunking with overlap
- ✅ Semantic search via embeddings
- ✅ Metadata filtering
- ✅ Similarity scoring
- ✅ Ready for Chroma integration
- ✅ Async throughout

#### 8. **Repository Pattern** (`src/repositories/`)
```python
"""
Repository Pattern Implementation
================================
Clean separation between business logic and data access.
"""
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.database.models import Article
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseRepository(ABC):
    """Abstract base repository."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def create(self, entity: Any) -> Any:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def update(self, id: str, updates: Dict) -> Optional[Any]:
        """Update entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity."""
        pass


class ArticleRepository(BaseRepository):
    """
    Article data access layer.
    
    Handles all database operations for articles with proper
    error handling, transaction management, and query optimization.
    """
    
    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db
    
    async def get_by_id(self, id: str) -> Optional[Article]:
        """Get article by ID."""
        try:
            return self.db.query(Article).filter(Article.id == id).first()
        except Exception as e:
            logger.error(f"Error fetching article {id}: {e}")
            return None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> List[Article]:
        """Get articles with pagination and filters."""
        try:
            query = self.db.query(Article)
            
            # Apply filters
            if filters:
                if filters.get("source"):
                    query = query.filter(Article.source == filters["source"])
                if filters.get("date_from"):
                    query = query.filter(Article.published_date >= filters["date_from"])
            
            return query.offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return []
    
    async def create(self, article_data: Dict) -> Optional[Article]:
        """Create new article."""
        try:
            article = Article(**article_data)
            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)
            return article
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating article: {e}")
            return None
    
    async def search_by_embedding(
        self, 
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Article]:
        """Semantic search using embeddings."""
        # Implementation with vector similarity
        pass
```

**Key Points**:
- ✅ Repository pattern for clean architecture
- ✅ Abstract base for consistency
- ✅ Proper transaction management
- ✅ Error handling and rollback
- ✅ Query optimization
- ✅ Support for semantic search

### Testing Standards

#### Backend Testing Structure
```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and test configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_article_repository.py
│   ├── test_embedding_repository.py
│   ├── test_embedding_service.py
│   ├── test_news_service.py
│   ├── test_summarization_service.py
│   ├── test_health_routes.py
│   ├── test_search_routes.py
│   └── test_models.py
├── integration/             # Integration tests (API + DB + Services)
│   ├── __init__.py
│   ├── test_news_api.py
│   ├── test_rag_pipeline.py
│   ├── test_embedding_flow.py
│   └── test_llm_providers.py
├── e2e/                     # End-to-end tests (full workflows)
│   ├── __init__.py
│   ├── test_complete_workflows.py
│   ├── test_scraping_to_display.py
│   └── test_semantic_search.py
├── fixtures/                # Test data and fixtures
│   ├── __init__.py
│   ├── article_fixtures.py
│   ├── test_data.py
│   └── mock_embeddings.py
└── helpers/                 # Test utilities
    ├── __init__.py
    ├── mock_helpers.py
    └── test_helpers.py
```

#### Example Test
```python
"""
Test Articles API Endpoints
===========================
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from backend.production_main import app
from backend.app.models import ArticleCreate


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        "title": "Test Article",
        "content": "Test content",
        "url": "https://example.com/test",
        "published_at": datetime.utcnow().isoformat(),
        "source": "hackernews"
    }


class TestArticlesEndpoint:
    """Test articles API endpoints."""
    
    def test_get_articles_success(self, client):
        """Test successful article retrieval."""
        response = client.get("/articles?page=1&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total" in data
        assert isinstance(data["articles"], list)
    
    def test_get_articles_pagination(self, client):
        """Test article pagination."""
        response = client.get("/articles?page=1&per_page=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) <= 5
        assert data["per_page"] == 5
    
    def test_get_articles_invalid_page(self, client):
        """Test invalid page parameter."""
        response = client.get("/articles?page=-1")
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_create_article(self, client, sample_article):
        """Test article creation."""
        response = client.post("/articles", json=sample_article)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == sample_article["title"]
        assert "id" in data
```

**Key Points**:
- ✅ Use pytest for testing
- ✅ Fixtures for reusable test data
- ✅ Test success and failure cases
- ✅ Test edge cases and validation
- ✅ Use TestClient for API testing
- ✅ Async tests with `@pytest.mark.asyncio`
- ✅ Clear test names describing what's tested

---

## 🎨 Frontend Development (React + TypeScript)

### Project Structure Convention
```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── ui/             # shadcn/ui components (40+ components)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── badge.tsx
│   │   │   └── ... (all shadcn/ui components)
│   │   ├── NewsCard.tsx           # News article display card
│   │   ├── SearchBar.tsx          # Search input component
│   │   ├── TopicFilter.tsx        # Category filter component
│   │   ├── DigestView.tsx         # Daily digest component
│   │   ├── ChatInterface.tsx      # AI chat component
│   │   ├── ResearchMode.tsx       # AI research component
│   │   └── KnowledgeGraph.tsx     # Graph visualization component
│   ├── config/             # Configuration files
│   │   └── api.ts          # FastAPI backend configuration
│   ├── styles/             # Global styles
│   │   └── globals.css     # Tailwind CSS + custom styles
│   ├── utils/              # Utility functions
│   ├── supabase/           # Legacy Supabase code (NOT USED - to be removed)
│   │   └── functions/      # Old Supabase Edge Functions
│   ├── App.tsx             # Root component (single-page app)
│   ├── main.tsx            # Entry point
│   └── index.css           # CSS entry
├── public/                 # Static assets
├── .env                    # Environment variables (VITE_API_BASE_URL)
├── package.json            # Dependencies (React 18, Vite, Tailwind)
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite configuration
└── tailwind.config.js      # Tailwind CSS configuration
```

**Key Architecture Notes**:
- 🎯 **Single-Page Application**: All features in one `App.tsx` with tabs (no routing)
- 🎨 **UI Library**: shadcn/ui components (40+ radix-ui based components)
- 🔗 **API Integration**: Direct fetch to FastAPI via `config/api.ts`
- 💾 **State Management**: React hooks + localStorage (no external state library)
- ⚠️ **Legacy Code**: `supabase/` folder exists but is NOT USED (to be removed)

### Coding Standards

#### 1. **Components**
```typescript
/**
 * ArticleCard Component
 * 
 * Displays a single article with title, source, summary, and actions.
 * 
 * @example
 * <ArticleCard 
 *   article={article} 
 *   onRead={handleRead}
 *   onSummarize={handleSummarize}
 * />
 */
import React, { useState, useCallback } from 'react';
import { ExternalLink, Bookmark, Clock } from 'lucide-react';
import type { Article } from '../types/api';
import { formatDate } from '../lib/utils';

interface ArticleCardProps {
  /** Article data to display */
  article: Article;
  /** Callback when article is marked as read */
  onRead?: (articleId: string) => void;
  /** Callback when summarize is requested */
  onSummarize?: (articleId: string) => Promise<void>;
  /** Whether the article is bookmarked */
  isBookmarked?: boolean;
  /** Custom className for styling */
  className?: string;
}

export default function ArticleCard({
  article,
  onRead,
  onSummarize,
  isBookmarked = false,
  className = ''
}: ArticleCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Memoized handlers
  const handleSummarize = useCallback(async () => {
    if (!onSummarize) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await onSummarize(article.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Summarization failed');
    } finally {
      setIsLoading(false);
    }
  }, [article.id, onSummarize]);
  
  const handleRead = useCallback(() => {
    if (onRead) {
      onRead(article.id);
    }
    // Open in new tab
    window.open(article.url, '_blank', 'noopener,noreferrer');
  }, [article.id, article.url, onRead]);
  
  return (
    <article 
      className={`
        bg-white rounded-lg shadow-md p-6 
        hover:shadow-lg transition-shadow duration-200
        ${className}
      `}
      aria-label={`Article: ${article.title}`}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            {article.title}
          </h3>
          
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="font-medium">{article.source}</span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {formatDate(article.published_at)}
            </span>
          </div>
        </div>
        
        <button
          onClick={() => {/* handle bookmark */}}
          className={`
            p-2 rounded-full transition-colors
            ${isBookmarked 
              ? 'text-blue-600 bg-blue-50' 
              : 'text-gray-400 hover:text-blue-600'
            }
          `}
          aria-label={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
        >
          <Bookmark className="w-5 h-5" />
        </button>
      </div>
      
      {/* Content */}
      <p className="text-gray-700 mb-4 line-clamp-3">
        {article.summary || article.content}
      </p>
      
      {/* Categories */}
      {article.categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {article.categories.map((category) => (
            <span
              key={category}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium"
            >
              {category}
            </span>
          ))}
        </div>
      )}
      
      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleRead}
          className="
            flex items-center gap-2 px-4 py-2 
            bg-blue-600 text-white rounded-md
            hover:bg-blue-700 transition-colors
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          "
        >
          <ExternalLink className="w-4 h-4" />
          Read Article
        </button>
        
        {onSummarize && (
          <button
            onClick={handleSummarize}
            disabled={isLoading}
            className="
              px-4 py-2 border border-gray-300 rounded-md
              hover:bg-gray-50 transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            "
          >
            {isLoading ? 'Summarizing...' : 'Summarize'}
          </button>
        )}
      </div>
      
      {/* Error message */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </article>
  );
}
```

**Key Points**:
- ✅ Comprehensive JSDoc comments
- ✅ Full TypeScript types for props
- ✅ Default props and optional props
- ✅ Error handling and loading states
- ✅ Accessibility (ARIA labels, keyboard navigation)
- ✅ Memoized callbacks with `useCallback`
- ✅ Semantic HTML
- ✅ Tailwind CSS for styling
- ✅ Proper event handling

#### 2. **Main App Component** (`App.tsx`)
The application is a **single-page app** with all features in one component using tabs:

```typescript
/**
 * Main App Component
 * 
 * Single-page application with tabbed interface for all features.
 * NO ROUTING - all features accessible via tabs.
 */
import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { API_ENDPOINTS, apiFetch } from './config/api';
import NewsCard from './components/NewsCard';
import DigestView from './components/DigestView';
import ChatInterface from './components/ChatInterface';
import ResearchMode from './components/ResearchMode';
import KnowledgeGraph from './components/KnowledgeGraph';

export default function App() {
  const [articles, setArticles] = useState<any[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [digest, setDigest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Fetch articles from FastAPI backend
  const fetchArticles = async () => {
    try {
      const params = new URLSearchParams({
        limit: '50',
        offset: '0',
        ...(selectedCategories.length > 0 && { 
          categories: selectedCategories.join(',') 
        }),
        ...(searchQuery && { search: searchQuery })
      });
      
      const response = await apiFetch(`${API_ENDPOINTS.news}?${params}`);
      
      // Transform response format (FastAPI returns {items: [...]} but we need {articles: [...]})
      const articlesData = response.items || response.articles || [];
      setArticles(articlesData);
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Save preferences to localStorage (no backend endpoint yet)
  const savePreferences = async (categories: string[]) => {
    try {
      localStorage.setItem('selectedCategories', JSON.stringify(categories));
      setSelectedCategories(categories);
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };
  
  useEffect(() => {
    fetchArticles();
  }, [selectedCategories, searchQuery]);
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Tabs defaultValue="feed">
        <TabsList>
          <TabsTrigger value="feed">News Feed</TabsTrigger>
          <TabsTrigger value="research">Research</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge</TabsTrigger>
          <TabsTrigger value="digest">Digest</TabsTrigger>
          <TabsTrigger value="chat">Ask AI</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        
        <TabsContent value="feed">
          {/* News feed with filters */}
        </TabsContent>
        
        <TabsContent value="digest">
          <DigestView digest={digest} />
        </TabsContent>
        
        {/* Other tabs... */}
      </Tabs>
    </div>
  );
}

**Key Points**:
- ✅ Single-page application with tab-based navigation
- ✅ All state managed with React hooks (useState, useEffect)
- ✅ localStorage for preferences (no backend auth yet)
- ✅ Direct fetch calls to FastAPI endpoints
- ✅ Response transformation for API compatibility
- ✅ Mock data for features without backend implementation
- ✅ Yellow background design system (Figma TechPulse AI)

#### 3. **API Client** (`config/api.ts`)
```typescript
/**
 * API Configuration for FastAPI Backend
 * 
 * This file configures the connection to the FastAPI backend.
 * NO AUTHENTICATION - using direct fetch with localStorage for preferences.
 */

// Get API base URL from environment or use default
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // News endpoints
  news: '/api/news',
  newsById: (id: string) => `/api/news/${id}`,
  newsSearch: '/api/news/search',
  newsIngest: '/api/news/ingest',
  newsSources: '/api/news/sources',
  newsStats: '/api/news/stats',
  
  // Search endpoints
  search: '/api/search',
  semanticSearch: '/api/search/semantic',
  
  // Summarization endpoints
  summarize: '/api/summarization/summarize',
  summarizeBatch: '/api/summarization/batch',
  
  // Embeddings endpoints
  embeddings: '/api/embeddings/generate',
  embeddingsStats: '/api/embeddings/stats',
  
  // Health check
  health: '/health',
  healthDetailed: '/health/detailed',
};

/**
 * Fetch wrapper with error handling
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, {
    ...defaultOptions,
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP error! status: ${response.status}`,
    }));
    throw new Error(error.detail || `API request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Example usage in components:
 */

// Fetch all news
const newsData = await apiFetch(`${API_ENDPOINTS.news}?limit=20&offset=0`);

// Semantic search
const searchResults = await apiFetch(API_ENDPOINTS.semanticSearch, {
  method: 'POST',
  body: JSON.stringify({ query: 'AI developments' })
});

// Get health status
const health = await apiFetch(API_ENDPOINTS.health);
```

**Key Points**:
- ✅ Centralized API configuration with all endpoints defined
- ✅ Native `fetch` API (no axios dependency)
- ✅ Simple error handling with try/catch
- ✅ TypeScript generic support with `apiFetch<T>`
- ✅ Environment-based configuration (VITE_API_BASE_URL)
- ✅ No authentication (using localStorage for preferences)
- ✅ Direct integration with FastAPI backend

#### 4. **Type Definitions**
```typescript
/**
 * API Type Definitions
 * 
 * Shared types between frontend and backend.
 * Keep in sync with backend Pydantic models.
 */

/** Article model */
export interface Article {
  id: string;
  title: string;
  content: string;
  url: string;
  published_at: string;
  source: string;
  source_id?: string;
  categories: string[];
  keywords: string[];
  ai_summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  created_at: string;
  updated_at: string;
}

/** Article search parameters */
export interface ArticleSearchParams {
  query?: string;
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
  published_after?: string;
  published_before?: string;
}

/** Search response */
export interface SearchResponse {
  articles: Article[];
  total: number;
  limit: number;
  offset: number;
  query?: string;
}

/** Health status */
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  components: {
    database: string;
    scrapers: string;
    api: string;
  };
  uptime_seconds: number;
}

/** Error response */
export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}
```

**Key Points**:
- ✅ Mirror backend models
- ✅ Use strict types (no `any`)
- ✅ Document all interfaces
- ✅ Use union types for enums
- ✅ Optional fields marked with `?`

### Testing Standards

#### Frontend Testing Structure
```
frontend/src/
├── __tests__/
│   ├── components/
│   │   ├── ArticleCard.test.tsx
│   │   └── SearchBar.test.tsx
│   ├── hooks/
│   │   └── useArticles.test.ts
│   └── utils/
│       └── utils.test.ts
├── setupTests.ts
└── testUtils.tsx
```

#### Example Test
```typescript
/**
 * ArticleCard Component Tests
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ArticleCard from '../components/ArticleCard';
import type { Article } from '../types/api';

const mockArticle: Article = {
  id: '1',
  title: 'Test Article',
  content: 'Test content',
  url: 'https://example.com',
  published_at: '2025-10-06T12:00:00Z',
  source: 'hackernews',
  categories: ['AI', 'ML'],
  keywords: ['test'],
  created_at: '2025-10-06T12:00:00Z',
  updated_at: '2025-10-06T12:00:00Z'
};

describe('ArticleCard', () => {
  it('renders article information', () => {
    render(<ArticleCard article={mockArticle} />);
    
    expect(screen.getByText('Test Article')).toBeInTheDocument();
    expect(screen.getByText('hackernews')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });
  
  it('calls onRead when read button is clicked', () => {
    const onRead = vi.fn();
    render(<ArticleCard article={mockArticle} onRead={onRead} />);
    
    const readButton = screen.getByText('Read Article');
    fireEvent.click(readButton);
    
    expect(onRead).toHaveBeenCalledWith('1');
  });
  
  it('shows loading state when summarizing', async () => {
    const onSummarize = vi.fn(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<ArticleCard article={mockArticle} onSummarize={onSummarize} />);
    
    const summarizeButton = screen.getByText('Summarize');
    fireEvent.click(summarizeButton);
    
    expect(screen.getByText('Summarizing...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Summarize')).toBeInTheDocument();
    });
  });
});
```

---

## 🧪 Testing Strategy

### Testing Pyramid
```
        /\
       /E2E\       (Few) - Full user flows
      /------\
     /Integr-\    (Some) - API + DB + Services
    /----------\
   /   Unit    \  (Many) - Functions, components
  /--------------\
```

### Coverage Requirements
- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Critical paths
- **E2E Tests**: Main user journeys

### Test Organization Structure

**CRITICAL**: All tests must be organized in the proper folder structure. Duplicates at root level are NOT allowed.

```
backend/tests/
├── conftest.py              # Global fixtures and configuration
├── fixtures/                # Shared test data and fixtures
│   ├── article_fixtures.py  # Article data generators
│   ├── news_service_fixtures.py
│   └── test_data.py
├── helpers/                 # Test utilities (NOT test files)
│   ├── mock_helpers.py      # Mock/patch utilities
│   └── test_helpers.py      # Assertion helpers
├── unit/                    # ✅ UNIT TESTS (11 files - 139+ tests)
│   ├── test_models.py                    # Pydantic models validation
│   ├── test_article_repository.py        # Repository pattern tests
│   ├── test_news_service.py              # NewsService business logic
│   ├── test_embedding_service.py         # Embedding generation
│   ├── test_health_routes.py             # Health check endpoints
│   ├── test_core_functionality.py        # Core utilities
│   ├── test_error_handling_framework.py  # Error handling patterns
│   ├── test_final_coverage_push.py       # Coverage validation
│   ├── test_news_service_fixes.py        # Additional service tests
│   ├── test_app_startup.py               # App initialization
│   └── test_ci_environment.py            # CI/CD environment tests
├── integration/             # ✅ INTEGRATION TESTS (3 files)
│   ├── test_news_api.py                  # News API + DB integration
│   ├── test_search_api.py                # Search + Vector DB
│   └── test_ingestion_integration.py     # Full ingestion flow
├── services/                # Service-specific tests (1 file)
│   └── test_ingestion_service.py         # Ingestion service tests
├── e2e/                     # END-TO-END TESTS (1 file)
│   └── test_complete_workflows.py        # Complete user workflows
└── api/                     # API route tests (currently empty)
```

**📋 Current Test Count: 11 unit + 3 integration + 1 e2e + 1 service = 16 test files**
**Tests Passing: 139+ unit tests**

### 📂 Additional Test Resources

Manual testing scripts (for local development, not pytest):
```
scripts/
├── test_content_parser.py      # Content parsing verification
├── test_embeddings.py          # Embedding generation testing
├── test_ingestion.py           # Ingestion system testing
├── test_ollama_integration.py  # Ollama provider testing
├── test_rss.py                 # RSS feed parsing testing
└── test_summarization.py       # LLM summarization testing
```

**Note**: These scripts are for manual testing and experimentation. They use direct execution (e.g., `python scripts/test_ollama_integration.py`) and are NOT run by pytest CI/CD.

### ⚠️ IMPORTANT: No Root-Level Test Files

**STRICT ENFORCEMENT**: Test files at `backend/test_*.py` (root level) are **NOT ALLOWED**.

**Why?**
- Clutters the backend directory
- Breaks pytest discovery and organization
- Makes maintenance difficult
- Violates Clean Architecture principles

**What to do instead:**
- ✅ **Unit tests** → `backend/tests/unit/test_*.py`
- ✅ **Integration tests** → `backend/tests/integration/test_*.py`
- ✅ **E2E tests** → `backend/tests/e2e/test_*.py`
- ✅ **Manual test scripts** → `backend/scripts/test_*.py` (not run by pytest)

**Historical cleanup (2025-10-22):**
- Removed 13 root-level test files
- Moved test_ci.py → tests/unit/test_ci_environment.py
- Moved manual testing scripts to scripts/ folder
- Deleted 6 obsolete debug files

### Test Types

#### 1. Unit Tests (`tests/unit/`)
Location: `backend/tests/unit/test_*.py`

What to test:
- Individual functions and methods
- Service business logic
- Repository data access patterns
- Model validation (Pydantic)
- Error handling utilities
- Core utilities

Example:
```python
# tests/unit/test_news_service.py
class TestNewsService:
    def test_fetch_articles_success(self):
        """Test successful article fetching"""
        pass
```

#### 2. Integration Tests (`tests/integration/`)
Location: `backend/tests/integration/test_*.py`

What to test:
- API endpoints + database (real or mocked DB)
- Service orchestration (multiple services together)
- Vector database + search functionality
- End-to-end data flows

Example:
```python
# tests/integration/test_news_api.py
class TestNewsRoutes:
    def test_get_articles_with_pagination(self, client):
        """Test API pagination with real DB"""
        pass
```

#### 3. Service Tests (`tests/services/`)
Location: `backend/tests/services/test_*.py`

What to test:
- Complex service logic
- Multiple component interactions
- Business rule validation

Example:
```python
# tests/services/test_ingestion_service.py
class TestIngestionService:
    def test_ingest_rss_feed(self):
        """Test RSS feed ingestion"""
        pass
```

#### 4. E2E Tests (`tests/e2e/`)
Location: `backend/tests/e2e/test_*.py`

What to test:
- Complete user workflows
- Multiple API calls in sequence
- Data consistency across operations
- Error recovery flows

Example:
```python
# tests/e2e/test_complete_workflows.py
class TestCompleteWorkflows:
    async def test_news_ingestion_to_search(self):
        """Test ingest → store → search flow"""
        pass
```

### File Organization Rules

⚠️ **MUST FOLLOW THESE RULES**:

1. **NO test files at `tests/` root level**
   - ❌ `tests/test_*.py` - Not allowed
   - ✅ `tests/unit/test_*.py` - Correct
   - ✅ `tests/integration/test_*.py` - Correct

2. **No duplicate tests**
   - Delete old versions when refactoring
   - Move tests to proper folder
   - Don't keep multiple copies

3. **Shared utilities go in `helpers/` or `fixtures/`**
   - ❌ `tests/shared_mocks.py` - Wrong
   - ✅ `tests/helpers/mock_helpers.py` - Correct

4. **All tests must import conftest fixtures**
   ```python
   # Good - Uses global fixtures
   def test_something(mock_db, mock_service):
       pass
   
   # Bad - Creates local fixtures
   @pytest.fixture
   def local_fixture():
       pass
   ```

---

## 🤖 AI/ML Specific Guidelines

### Vector Embeddings Best Practices
1. **Model Selection**: Choose appropriate embedding model based on use case
   - `all-MiniLM-L6-v2`: Fast, lightweight (384 dims) for general search
   - `all-mpnet-base-v2`: Higher quality (768 dims) for precise retrieval
   - Multilingual models for multi-language support

2. **Batch Processing**: Always process embeddings in batches for efficiency
   ```python
   # Good - Batch processing
   embeddings = await generator.generate_embeddings(texts, batch_size=32)
   
   # Bad - Individual processing
   for text in texts:
       embedding = await generator.generate_embeddings([text])
   ```

3. **Caching**: Cache embeddings to avoid recomputation
   - Store embeddings in vector database (Chroma)
   - Use in-memory cache for frequently accessed items
   - Set appropriate TTL based on content update frequency

4. **Dimension Reduction**: Consider dimensionality reduction for large-scale deployments
   - PCA for linear reduction
   - t-SNE/UMAP for visualization
   - Maintain 90%+ variance

### RAG Pipeline Best Practices
1. **Chunking Strategy**: 
   - Semantic chunking (preserve meaning boundaries)
   - Fixed-size chunks with overlap (50-100 chars)
   - Metadata preservation for filtering

2. **Retrieval Quality**:
   - Hybrid search (vector + keyword)
   - Reranking with cross-encoder models
   - Metadata filtering for domain-specific queries

3. **Context Window Management**:
   - Respect LLM token limits (4k, 8k, 16k, etc.)
   - Prioritize most relevant chunks
   - Include source attribution

4. **Performance Optimization**:
   - Pre-compute embeddings during ingestion
   - Use approximate nearest neighbor (ANN) for large datasets
   - Implement caching at multiple levels

### LLM Integration Best Practices
1. **Provider Abstraction**: Always use provider abstraction layer
   ```python
   # Good - Provider agnostic
   provider = get_llm_provider()  # Can be Ollama, Claude, OpenAI
   result = await provider.summarize(text)
   
   # Bad - Direct provider coupling
   response = openai.ChatCompletion.create(...)
   ```

2. **Error Handling & Fallbacks**:
   ```python
   async def get_summary(text: str) -> str:
       providers = [OllamaProvider(), ClaudeProvider(), OpenAIProvider()]
       
       for provider in providers:
           try:
               if await provider.is_available():
                   result = await provider.summarize(text)
                   if result["success"]:
                       return result["summary"]
           except Exception as e:
               logger.warning(f"Provider {provider} failed: {e}")
               continue
       
       return "Summary unavailable"
   ```

3. **Prompt Engineering**:
   - Use template-based prompts
   - Include examples (few-shot learning)
   - Specify output format clearly
   - Handle edge cases in prompts

4. **Cost & Performance Optimization**:
   - Cache common queries
   - Batch requests when possible
   - Use cheaper models for simple tasks
   - Implement rate limiting
   - Monitor token usage

### ChromaDB Integration (Vector Database)
```python
"""
ChromaDB Integration for Production
==================================
"""
import chromadb
from chromadb.config import Settings

class VectorStore:
    """Production-ready vector store with ChromaDB."""
    
    def __init__(self, collection_name: str = "articles"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./data/chroma"
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Distance metric
        )
    
    async def add_documents(
        self, 
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents with embeddings to vector store."""
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    async def search(
        self, 
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Search for similar documents."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where  # Metadata filtering
        )
```

### Testing AI/ML Components
1. **Unit Tests for ML Code**:
   ```python
   def test_embedding_generation():
       """Test embedding generation produces correct dimensions."""
       generator = EmbeddingGenerator("all-MiniLM-L6-v2")
       texts = ["test article 1", "test article 2"]
       
       embeddings = await generator.generate_embeddings(texts)
       
       assert embeddings.shape == (2, 384)  # Correct dimensions
       assert np.all(np.linalg.norm(embeddings, axis=1) > 0)  # Non-zero
   ```

2. **Integration Tests for RAG**:
   ```python
   @pytest.mark.integration
   async def test_rag_pipeline_end_to_end():
       """Test complete RAG pipeline."""
       rag = RAGPipeline(embedding_generator)
       
       # Add documents
       docs = [{"content": "AI news article", "id": "1"}]
       await rag.add_documents(docs)
       
       # Search
       results = await rag.search("artificial intelligence")
       
       assert len(results) > 0
       assert results[0]["score"] > 0.5
   ```

3. **Mock LLM Responses**:
   ```python
   @pytest.fixture
   def mock_llm_provider(monkeypatch):
       """Mock LLM provider for testing."""
       async def mock_summarize(self, text: str, **kwargs):
           return {
               "summary": "Test summary",
               "success": True,
               "model": "test-model"
           }
       
       monkeypatch.setattr(OllamaProvider, "summarize", mock_summarize)
   ```

---

## 🚀 Feature Implementation Guidelines

### Adding New Features - Step by Step

#### 1. **Planning Phase**
```markdown
Feature: Advanced Search with Filters

Requirements:
- Filter by date range
- Filter by multiple categories
- Sort by relevance/date
- Save search preferences

Technical Design:
- Backend: New query parameters in /search endpoint
- Frontend: SearchFilters component
- State: useSearchFilters hook
- Storage: Save to user preferences
```

#### 2. **Backend Implementation**
```
1. Update models (if needed)
   - Add new Pydantic schemas
   - Update SQLAlchemy models

2. Create/update service layer
   - Add business logic
   - Database queries with new filters

3. Create/update API endpoints
   - Add new route or update existing
   - Input validation
   - Error handling

4. Write tests
   - Unit tests for service methods
   - Integration tests for endpoints

5. Update documentation
   - API docs (automatic with FastAPI)
   - README if needed
```

#### 3. **Frontend Implementation**
```
1. Define types
   - Update types/api.ts
   - Add new interfaces

2. Update API client
   - Add new API methods
   - Type all requests/responses

3. Create UI components
   - Follow component structure
   - Add accessibility
   - Error states

4. Create custom hooks (if needed)
   - State management
   - API integration

5. Write tests
   - Component tests
   - Hook tests
   - Integration tests

6. Update documentation
```

### Example: Adding Comment System

#### Backend
```python
# 1. Model (app/models/__init__.py)
class CommentDB(Base):
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True)
    article_id = Column(String, ForeignKey("articles.id"))
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

# 2. Service (app/services/comment_service.py)
class CommentService:
    async def create_comment(
        self, 
        article_id: str, 
        user_id: str, 
        content: str
    ) -> Comment:
        # Validation, business logic
        pass
    
    async def get_comments(
        self, 
        article_id: str, 
        limit: int = 50
    ) -> List[Comment]:
        # Fetch and return comments
        pass

# 3. API Endpoint (app/api/endpoints.py)
@router.post("/articles/{article_id}/comments")
async def create_comment(
    article_id: str,
    content: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on an article."""
    return await comment_service.create_comment(
        article_id, current_user.id, content
    )

# 4. Tests (tests/test_api/test_comments.py)
def test_create_comment(client, auth_token):
    response = client.post(
        "/articles/123/comments",
        json={"content": "Great article!"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
```

#### Frontend
```typescript
// 1. Types (types/api.ts)
export interface Comment {
  id: string;
  article_id: string;
  user_id: string;
  content: string;
  created_at: string;
}

// 2. API Client (lib/api.ts)
export const commentsApi = {
  getComments: async (articleId: string): Promise<Comment[]> => {
    const response = await api.get(`/articles/${articleId}/comments`);
    return response.data;
  },
  
  createComment: async (
    articleId: string, 
    content: string
  ): Promise<Comment> => {
    const response = await api.post(
      `/articles/${articleId}/comments`,
      { content }
    );
    return response.data;
  }
};

// 3. Hook (hooks/useComments.ts)
export function useComments(articleId: string) {
  return useQuery({
    queryKey: ['comments', articleId],
    queryFn: () => commentsApi.getComments(articleId)
  });
}

// 4. Component (components/CommentSection.tsx)
export default function CommentSection({ articleId }: Props) {
  const { data: comments } = useComments(articleId);
  const [content, setContent] = useState('');
  
  const createMutation = useMutation({
    mutationFn: () => commentsApi.createComment(articleId, content),
    onSuccess: () => {
      queryClient.invalidateQueries(['comments', articleId]);
      setContent('');
    }
  });
  
  return (
    <div>
      {/* Comment list */}
      {/* Comment form */}
    </div>
  );
}
```

---

## 🔒 Security Best Practices

### Backend Security
1. **Input Validation**: Use Pydantic models for all inputs
2. **SQL Injection**: Use SQLAlchemy ORM, never raw SQL
3. **Authentication**: JWT tokens with proper expiration
4. **Password Hashing**: bcrypt with salt
5. **CORS**: Strict origin whitelist
6. **Rate Limiting**: Implement on all endpoints
7. **HTTPS**: Always in production
8. **Environment Variables**: Never commit secrets

### Frontend Security
1. **XSS Prevention**: React escapes by default, never use `dangerouslySetInnerHTML`
2. **CSRF**: Include CSRF tokens for mutations
3. **Token Storage**: Use httpOnly cookies (not localStorage for sensitive data)
4. **Input Sanitization**: Validate all user inputs
5. **Dependency Scanning**: Regular `npm audit`
6. **Content Security Policy**: Configure CSP headers

---

## 📊 Performance Best Practices

### Backend Performance
1. **Database Indexing**: Index all foreign keys and frequently queried fields
2. **Connection Pooling**: Configure pool size based on load
3. **Caching**: Redis for frequently accessed data
4. **Async Operations**: Use async/await for all I/O
5. **Pagination**: Always paginate large result sets
6. **Query Optimization**: Use `select_related` and `prefetch_related`
7. **Background Tasks**: Use FastAPI BackgroundTasks for non-critical operations

### Frontend Performance
1. **Code Splitting**: Lazy load routes and heavy components
2. **Memoization**: Use `useMemo` and `useCallback` appropriately
3. **Virtual Scrolling**: For long lists
4. **Image Optimization**: Lazy loading, modern formats
5. **Bundle Size**: Monitor and optimize
6. **Caching**: Use TanStack Query's caching effectively
7. **Debouncing**: For search inputs

---

## 📝 Documentation Standards

### Code Documentation
- **Python**: Google-style docstrings
- **TypeScript**: JSDoc comments
- **API**: Automatic with FastAPI (OpenAPI/Swagger)

### Project Documentation
- **README.md**: Overview, quick start, features
- **CONTRIBUTING.md**: How to contribute
- **API_DOCS.md**: Detailed API documentation
- **ARCHITECTURE.md**: System design and architecture

---

## ✍️ Writing Tests - Guidelines by Location

### 1. **Unit Tests** (`tests/unit/test_*.py`)

Purpose: Test individual functions, methods, and services in isolation.

**When to create unit tests:**
- New service methods
- New utility functions
- Model validation (Pydantic)
- Repository methods
- Error handling logic

**What to test:**
```python
# tests/unit/test_news_service.py
import pytest
from src.services.news_service import NewsService
from tests.fixtures.article_fixtures import sample_article

class TestNewsService:
    """Test NewsService methods."""
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock DB."""
        return NewsService(db=mock_db)
    
    def test_fetch_articles_success(self, service):
        """Test successful article fetching."""
        # Setup
        articles = [sample_article(), sample_article()]
        service.db.query.return_value = articles
        
        # Execute
        result = service.fetch_articles(limit=10)
        
        # Assert
        assert len(result) == 2
        assert result[0].title == articles[0].title
        service.db.query.assert_called_once()
    
    def test_fetch_articles_empty_database(self, service):
        """Test with empty database."""
        service.db.query.return_value = []
        
        result = service.fetch_articles(limit=10)
        
        assert result == []
    
    def test_fetch_articles_database_error(self, service):
        """Test error handling."""
        service.db.query.side_effect = Exception("DB Error")
        
        with pytest.raises(Exception):
            service.fetch_articles(limit=10)
    
    @pytest.mark.parametrize("limit,expected_calls", [(10, 1), (50, 1), (100, 1)])
    def test_fetch_articles_limits(self, service, limit, expected_calls):
        """Test different limit values."""
        service.db.query.return_value = []
        
        service.fetch_articles(limit=limit)
        
        assert service.db.query.call_count == expected_calls
```

**Key practices:**
- Use `@pytest.fixture` for setup
- Use `@pytest.mark.parametrize` for multiple scenarios
- Mock external dependencies (database, API, services)
- Test success, failure, and edge cases
- Keep tests focused (one concept per test)

### 2. **Integration Tests** (`tests/integration/test_*.py`)

Purpose: Test components working together (API + database, multiple services, etc.).

**When to create integration tests:**
- API endpoint testing
- Service orchestration
- Database transactions
- RAG pipeline flows
- Vector search

**What to test:**
```python
# tests/integration/test_news_api.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from tests.fixtures.article_fixtures import sample_article

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def db_with_articles(db_session):
    """Create database with sample articles."""
    articles = [
        sample_article(title="AI Breakthrough"),
        sample_article(title="Tech News"),
    ]
    for article in articles:
        db_session.add(article)
    db_session.commit()
    return db_session

class TestNewsRoutes:
    """Test news API routes."""
    
    def test_get_articles_success(self, client, db_with_articles):
        """Test successful article retrieval."""
        response = client.get("/api/news?page=1&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert len(data["articles"]) >= 2
    
    def test_get_articles_pagination(self, client, db_with_articles):
        """Test pagination parameters."""
        response = client.get("/api/news?page=1&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 1
    
    def test_get_articles_invalid_params(self, client):
        """Test invalid parameters."""
        response = client.get("/api/news?page=-1")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_articles_semantic(self, client, db_with_articles):
        """Test semantic search endpoint."""
        response = client.post(
            "/api/search",
            json={"query": "artificial intelligence"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
```

**Key practices:**
- Use real or well-mocked database
- Test with TestClient (FastAPI)
- Test HTTP status codes and response format
- Test data persistence and retrieval
- Include error scenarios

### 3. **Service Tests** (`tests/services/test_*.py`)

Purpose: Test complex service logic and business rules.

**When to create service tests:**
- Complex service logic (ingestion, summarization, etc.)
- Multiple component interactions
- Business rule validation
- Data transformation

**What to test:**
```python
# tests/services/test_ingestion_service.py
import pytest
from src.services.ingestion_service import IngestionService
from unittest.mock import MagicMock

class TestIngestionService:
    """Test ingestion service."""
    
    @pytest.fixture
    def mock_scraper(self):
        """Mock RSS scraper."""
        return MagicMock()
    
    @pytest.fixture
    def service(self, mock_scraper, mock_db):
        """Create service with mocks."""
        service = IngestionService(
            scraper=mock_scraper,
            db=mock_db
        )
        return service
    
    def test_ingest_rss_feed_success(self, service):
        """Test successful RSS feed ingestion."""
        # Setup
        service.scraper.fetch.return_value = [
            {"title": "Article 1", "url": "https://example.com/1"},
            {"title": "Article 2", "url": "https://example.com/2"}
        ]
        
        # Execute
        result = service.ingest_rss_feed("https://example.com/feed.xml")
        
        # Assert
        assert len(result) == 2
        assert result[0]["title"] == "Article 1"
        service.db.add.call_count == 2  # Two articles added
    
    def test_ingest_rss_feed_duplicate_handling(self, service):
        """Test duplicate article detection."""
        # Same URL should not be ingested twice
        articles = [
            {"title": "Article", "url": "https://example.com/1"}
        ]
        service.scraper.fetch.side_effect = [articles, articles]
        
        result1 = service.ingest_rss_feed("https://example.com/feed1.xml")
        result2 = service.ingest_rss_feed("https://example.com/feed2.xml")
        
        # Second ingestion should skip duplicate
        assert len(result1) == 1
        assert len(result2) == 0
    
    def test_ingest_rss_feed_error_handling(self, service):
        """Test error recovery during ingestion."""
        service.scraper.fetch.side_effect = ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            service.ingest_rss_feed("https://example.com/feed.xml")
        
        # Verify rollback or cleanup happened
        service.db.rollback.assert_called()
```

**Key practices:**
- Focus on business logic
- Mock only external services
- Test orchestration patterns
- Include error scenarios
- Test data consistency

### 4. **E2E Tests** (`tests/e2e/test_*.py`)

Purpose: Test complete user workflows end-to-end.

**When to create E2E tests:**
- Critical user workflows
- Data persistence across multiple operations
- Full feature flows

**What to test:**
```python
# tests/e2e/test_complete_workflows.py
import pytest
from fastapi.testclient import TestClient

class TestCompleteWorkflows:
    """Test complete user workflows."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from src.main import app
        return TestClient(app)
    
    def test_ingest_to_search_workflow(self, client):
        """Test complete workflow: ingest articles → search → retrieve."""
        # Step 1: Ingest articles
        ingest_response = client.post(
            "/api/news/ingest",
            json={"source": "hackernews"}
        )
        assert ingest_response.status_code == 200
        
        # Step 2: Verify articles in database
        list_response = client.get("/api/news?limit=10")
        assert list_response.status_code == 200
        articles_count = len(list_response.json()["articles"])
        assert articles_count > 0
        
        # Step 3: Search for articles
        search_response = client.post(
            "/api/search",
            json={"query": "technology"}
        )
        assert search_response.status_code == 200
        assert len(search_response.json()["results"]) > 0
        
        # Step 4: Verify data consistency
        first_result = search_response.json()["results"][0]
        detail_response = client.get(f"/api/news/{first_result['id']}")
        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == first_result["id"]
```

**Key practices:**
- Test complete workflows
- Verify data persistence
- Check state transitions
- Include cleanup/teardown
- Test real scenarios users would experience

---

---

## 🧪 TESTING REQUIREMENTS FOR NEW FEATURES

### **MANDATORY TESTING CHECKLIST - DO NOT SKIP**

> **CRITICAL**: Every new feature MUST have a complete test suite BEFORE any commit or push. Testing is NOT optional.

#### Backend Feature: Complete Test Suite Required

When adding new service/feature to backend, create tests for:

1. **Unit Tests** (80%+ coverage)
   - Test each public method
   - Test initialization and setup
   - Test success paths
   - Test error paths
   - Test edge cases
   - Use mocking for external dependencies

2. **Integration Tests**
   - Test with real or mocked database
   - Test service interactions
   - Test transaction management
   - Test error recovery

3. **API Endpoint Tests** (if applicable)
   - Test each endpoint
   - Test success (200, 201, etc.)
   - Test client errors (400, 422, etc.)
   - Test server errors (500)
   - Test error responses
   - Test request validation
   - Test response format

4. **Database Tests** (if applicable)
   - Test model constraints
   - Test unique constraints
   - Test foreign keys
   - Test transactions (commit/rollback)
   - Test migrations

#### Frontend Feature: Complete Test Suite Required

When adding new React component/feature, create tests for:

1. **Component Tests**
   - Test rendering
   - Test user interactions
   - Test prop variations
   - Test error states
   - Test loading states
   - Test accessibility (ARIA labels, keyboard nav)

2. **Hook Tests** (if applicable)
   - Test hook initialization
   - Test hook state updates
   - Test hook side effects
   - Test hook errors

3. **API Integration Tests**
   - Test API calls
   - Test data transformation
   - Test error handling
   - Test loading states

#### Test File Structure

```
backend/tests/
├── services/test_[service_name].py      # Unit tests for new service
├── api/test_[endpoint_name].py          # API endpoint tests
├── [feature_name]/
│   ├── test_[module1].py
│   ├── test_[module2].py
│   └── conftest.py                      # Fixtures for feature

frontend/src/__tests__/
├── components/[ComponentName].test.tsx  # Component tests
├── hooks/use[HookName].test.ts          # Hook tests
└── setupTests.ts                        # Test configuration
```

#### Test Execution Before Commit

```bash
# Backend - MUST pass before commit
cd backend
pytest tests/ -v --tb=short
pytest --cov=src --cov-report=term-missing tests/  # Check coverage

# Frontend - MUST pass before commit
cd frontend
npm test -- --coverage
npm run lint
```

#### Coverage Expectations

- **New Code**: 80%+ line coverage minimum
- **Service Classes**: 90%+ coverage expected
- **API Endpoints**: 100% coverage for all paths
- **Critical Paths**: 95%+ coverage (authentication, payment, data)

#### Example: Adding New Feature

**Scenario**: Add new `CategoryService.get_trending_categories()` method

**Required Tests**:
```python
# File: backend/tests/services/test_category_service.py

def test_get_trending_categories_success():
    """Test fetching trending categories."""
    # Setup, call, assert

def test_get_trending_categories_empty_db():
    """Test with no categories in database."""
    # Setup, call, assert

def test_get_trending_categories_limit():
    """Test respecting limit parameter."""
    # Setup, call, assert

def test_get_trending_categories_db_error():
    """Test handling database errors."""
    # Setup, call, assert
```

**Required Tests**:
```python
# File: backend/tests/api/test_category_routes.py

def test_get_trending_categories_endpoint():
    """Test GET /api/categories/trending endpoint."""
    # Setup, call, assert response

def test_get_trending_categories_pagination():
    """Test pagination parameters."""
    # Setup, call, assert

def test_get_trending_categories_error():
    """Test error response."""
    # Setup, call, assert error status
```

**MUST RUN BEFORE COMMIT**:
```bash
pytest backend/tests/services/test_category_service.py -v
pytest backend/tests/api/test_category_routes.py -v
pytest --cov=src.services.category_service backend/tests/
```

#### What NOT to Do

❌ **DO NOT commit code without tests**
- Exception: Testing code itself (conftest.py, fixtures, helpers)
- Exception: Auto-generated code (migrations, scaffolds)

❌ **DO NOT use placeholder tests**
- "# TODO: write tests" comments
- Empty test functions
- Tests that just import (no assertions)

❌ **DO NOT skip error/edge case testing**
- Only test happy paths
- Ignore validation failures
- Skip error response scenarios

❌ **DO NOT mock everything**
- Mock external services (APIs, third-party)
- Mock time/random for determinism
- Use real instances for unit-tested code

#### Test Maintenance

1. **Keep Tests Updated**
   - Update tests when modifying tested code
   - Update tests when changing API contracts
   - Update tests when modifying database schema

2. **Refactor Common Patterns**
   - Extract fixtures for reusable setup
   - Create helper functions for common assertions
   - Use parametrized tests for multiple scenarios

3. **Delete Obsolete Tests**
   - Remove tests for deleted features
   - Remove duplicate tests
   - Keep test suite lean

#### Testing Tools

**Backend**:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support
- `TestClient` (FastAPI) - API testing

**Frontend**:
- `vitest` - Testing framework
- `@testing-library/react` - Component testing
- `@testing-library/user-event` - User interaction
- `@testing-library/jest-dom` - DOM assertions

---

## ✅ Definition of Done

### Before any commit and push to remote branch:

1. **NEW FEATURES MUST HAVE TEST SUITE** ✅ **[REQUIRED FOR NEW FEATURES]**
   - Backend service/feature: Create `tests/services/test_[service].py` with 80%+ coverage
   - Backend API endpoints: Create `tests/api/test_[endpoint].py` with all paths tested
   - Frontend components: Create `src/__tests__/components/[Component].test.tsx` with user interactions
   - Frontend hooks: Create `src/__tests__/hooks/use[Hook].test.ts` if applicable
   - Database models: Create transaction/constraint tests if models changed
   - **NO EXCEPTIONS**: Every new feature MUST have tests before commit

2. **ALL TESTS MUST PASS** ✅ **[CRITICAL - BLOCKS COMMIT]**
   - Backend: Run `pytest tests/ -v` - **ALL** unit, integration, and CI tests must pass
   - Frontend: Run `npm test` - **ALL** component and integration tests must pass
   - CI/CD: All GitHub Actions checks must pass (ruff linting, mypy type checking, etc.)
   - If ANY test fails: DO NOT COMMIT - fix the test first
   - Coverage minimum: New code 80%, service classes 90%, API endpoints 100%

3. **Code Quality Checks** ✅
   - Backend: `ruff check .` - No linting errors
   - Backend: `mypy . --ignore-missing-imports` - Type checking passes
   - Frontend: `npm run lint` - ESLint passes
   - Frontend: `npx prettier --check` - Formatting is correct

4. **No Breaking Changes** ✅
   - Verify backward compatibility
   - Update API documentation if endpoints change
   - Update type definitions if models change

5. **Documentation Updated** ✅
   - Update inline code comments for complex logic
   - Update README if needed (with user approval only)
   - Update API documentation (auto-generated with FastAPI)
   - Update Copilot instructions if process changes

### Commands to Run Before Commit:

**Backend Testing:**
```bash
cd backend
pytest tests/ -v                          # Run all tests
ruff check .                               # Lint check
mypy . --ignore-missing-imports            # Type checking
```

**Frontend Testing:**
```bash
cd frontend
npm test                                   # Run all tests
npm run lint                               # ESLint check
npx prettier --check "src/**/*"            # Format check
```

**Full CI/CD Simulation (Local):**
```bash
# Backend
cd backend && python -m pytest test_ci.py -v --tb=short

# Frontend  
cd frontend && npm run lint && npm run build
```

### 🔄 Test Loop - MANDATORY BEFORE ANY COMMIT & PUSH

**CRITICAL REQUIREMENT**: When making ANY changes, Copilot MUST follow this loop until ALL tests pass:

1. **Run All Tests** (BEFORE making any changes)
   ```bash
   # Backend
   cd backend && python -m pytest tests/ -v
   
   # Frontend
   cd frontend && npm test
   ```

2. **Check Test Results**
   - ✅ ALL TESTS PASS? → Proceed to commit & push
   - ❌ TESTS FAIL? → Go to step 3 (LOOP)

3. **Fix Failing Tests** (LOOP CONTINUES HERE)
   - Analyze the failure messages
   - Identify root cause
   - Make code fixes
   - Re-run ONLY the failing tests to verify fix works
   - If fixed → Go to step 1 (re-run all tests)
   - If NOT fixed → Repeat step 3

4. **Verify All Tests Pass Again**
   - Re-run full test suite (step 1)
   - If any NEW tests fail → Loop back to step 3
   - If ALL tests pass → PROCEED TO COMMIT

5. **ONLY THEN: Commit & Push**
   - Once ALL tests verified passing
   - Commit with descriptive message
   - Push to remote branch
   - GitHub Actions CI/CD will run final verification

**IMPORTANT**:
- ❌ **NEVER commit or push if any tests fail**
- ❌ **NEVER skip test verification to save time**
- ✅ **Always loop until 100% test success**
- ✅ **Document what was fixed in commit message**

**If Tests Continue to Fail**:
- Provide detailed error messages and stack traces to user
- Ask for clarification on expected behavior
- Do NOT force-commit broken code
- Keep iterating on fixes

---

## 🔄 Git Workflow

### Branch Naming
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

### Commit Messages
```
type(scope): Brief description

Detailed explanation if needed.

- Change 1
- Change 2
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No console errors
```

---

## ⚡ Quick Reference

### Common Commands

**Backend**
```bash
# Start server
python backend/production_main.py

# Run tests
pytest tests/ -v

# Database migration
alembic upgrade head

# Install dependencies
pip install -r backend/requirements.txt
```

**Frontend**
```bash
# Start dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Install dependencies
npm install
```

---

## 🎓 Learning Resources

### Backend (FastAPI)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Frontend (React)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TanStack Query Documentation](https://tanstack.com/query/)

### Best Practices
- [12 Factor App](https://12factor.net/)
- [Clean Code](https://github.com/ryanmcdermott/clean-code-javascript)
- [API Design Guide](https://github.com/microsoft/api-guidelines)

---

## 🤖 AI Assistant Behavior

When GitHub Copilot assists with this project:

1. **Always follow these conventions** - Structure, naming, patterns
2. **Generate complete, production-ready code** - No TODOs or placeholders
3. **Include comprehensive error handling** - Try/catch, proper HTTP codes, fallbacks
4. **Add proper types everywhere** - Python type hints, TypeScript types
5. **Write meaningful comments** - Explain why, not what
6. **Consider security implications** - Validate inputs, handle auth, sanitize data
7. **Optimize for performance** - Async operations, caching, pagination, batch processing
8. **Include tests** - Suggest tests for new features, especially AI/ML components
9. **Follow accessibility standards** - ARIA labels, keyboard navigation
10. **Be consistent** - Match existing code style and patterns

**🔴 CRITICAL TEST LOOP REQUIREMENT**:
11. **RUN ALL TESTS BEFORE COMMIT** - This is NON-NEGOTIABLE
    - Before making ANY changes: Run full test suite (pytest + npm test)
    - After making changes: Re-run ALL tests
    - If ANY test fails: Keep fixing until ALL tests pass
    - NEVER commit or push with failing tests
    - NEVER skip tests to save time
    - Use the Test Loop process (see Definition of Done section)
    - Document test fixes in commit messages

12. **AI/ML specific**:
    - Always use provider abstraction for LLM calls
    - Implement graceful fallbacks for ML operations
    - Cache embeddings and LLM responses appropriately
    - Consider token limits and API costs
    - Handle model loading errors gracefully
    - Mock external AI services in tests
    - Document model assumptions and limitations
13. **RAG/Vector Search specific**:
    - Use semantic chunking for documents
    - Implement hybrid search (vector + keyword)
    - Add metadata filtering capabilities
    - Optimize for embedding generation performance
    - Consider storage and retrieval scalability

---

## 📋 Checklists

### New Feature Checklist
- [ ] Requirements documented
- [ ] Technical design reviewed
- [ ] Backend models created/updated
- [ ] Backend service layer implemented
- [ ] Backend API endpoints created
- [ ] Backend tests written (80%+ coverage)
- [ ] Frontend types defined
- [ ] Frontend API client updated
- [ ] Frontend components created
- [ ] Frontend hooks created (if needed)
- [ ] Frontend tests written
- [ ] Error handling implemented
- [ ] Loading states implemented
- [ ] Accessibility checked
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] CI/CD passing

### AI/ML Feature Checklist
- [ ] Model selection justified and documented
- [ ] Provider abstraction implemented
- [ ] Fallback mechanisms in place
- [ ] Error handling for model failures
- [ ] Response caching implemented
- [ ] Token usage monitored
- [ ] API rate limiting configured
- [ ] Embedding dimensions validated
- [ ] Vector search performance tested
- [ ] RAG pipeline chunking optimized
- [ ] Context window limits respected
- [ ] Model loading tested (cold start)
- [ ] ML operations properly mocked in tests
- [ ] Cost implications documented
- [ ] Performance benchmarks recorded

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] No console errors/warnings
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Error tracking setup (Sentry)
- [ ] Performance monitoring enabled
- [ ] Backup strategy in place
- [ ] SSL/TLS configured
- [ ] Documentation updated
- [ ] Smoke tests passed

---

**Version**: 2.0.0  
**Last Updated**: October 6, 2025  
**Maintainer**: Project Team

