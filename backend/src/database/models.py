"""
SQLAlchemy ORM Models
====================

Database models for the AI Tech News Assistant using SQLAlchemy ORM.
Provides type-safe database operations and relationships.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, VARCHAR

from .base import Base


class JSONEncodedDict(TypeDecorator):
    """Custom SQLAlchemy type for storing JSON data."""
    
    impl = VARCHAR
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


# Association table for many-to-many relationship between articles and categories
article_category_association = Table(
    'article_categories',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Index('idx_article_category_article', 'article_id'),
    Index('idx_article_category_category', 'category_id'),
)


class User(Base):
    """User model for authentication and personalization."""
    
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONEncodedDict)
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_active', 'is_active'),
    )


class Source(Base):
    """News source model."""
    
    __tablename__ = 'sources'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    rss_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scrape_frequency: Mapped[int] = mapped_column(Integer, default=3600)  # seconds
    last_scraped: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    source_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONEncodedDict)
    
    # Relationships
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="source")
    
    # Indexes
    __table_args__ = (
        Index('idx_sources_name', 'name'),
        Index('idx_sources_active', 'is_active'),
        Index('idx_sources_last_scraped', 'last_scraped'),
    )


class Category(Base):
    """Article category model."""
    
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Many-to-many relationship with articles
    articles: Mapped[List["Article"]] = relationship(
        "Article", 
        secondary=article_category_association, 
        back_populates="categories"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_categories_name', 'name'),
        Index('idx_categories_slug', 'slug'),
        Index('idx_categories_active', 'is_active'),
    )


class Article(Base):
    """Article model with full metadata and relationships."""
    
    __tablename__ = 'articles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(200))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Content metadata
    language: Mapped[Optional[str]] = mapped_column(String(10), default='en')
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    reading_time: Mapped[Optional[int]] = mapped_column(Integer)  # minutes
    
    # Status and engagement
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    
    # AI processing flags
    embedding_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sources.id'))
    
    # Additional metadata (JSON)
    article_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONEncodedDict)
    
    # Relationships
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="articles")
    categories: Mapped[List["Category"]] = relationship(
        "Category", 
        secondary=article_category_association, 
        back_populates="articles"
    )
    embeddings: Mapped[List["Embedding"]] = relationship("Embedding", back_populates="article")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_articles_url', 'url'),
        Index('idx_articles_title', 'title'),
        Index('idx_articles_published_at', 'published_at'),
        Index('idx_articles_created_at', 'created_at'),
        Index('idx_articles_source_id', 'source_id'),
        Index('idx_articles_archived', 'is_archived'),
        Index('idx_articles_featured', 'is_featured'),
        Index('idx_articles_embedding_generated', 'embedding_generated'),
        Index('idx_articles_summary_generated', 'summary_generated'),
        Index('idx_articles_compound_status', 'is_archived', 'is_featured'),
        Index('idx_articles_compound_processing', 'embedding_generated', 'summary_generated'),
    )


class Embedding(Base):
    """Vector embedding model for semantic search."""
    
    __tablename__ = 'embeddings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey('articles.id'), nullable=False)
    
    # Embedding data
    embedding_vector: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of float array
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Content metadata
    content_type: Mapped[str] = mapped_column(String(50), default='full_content', nullable=False)  # full_content, title, summary
    chunk_index: Mapped[Optional[int]] = mapped_column(Integer, default=0)  # For chunked content
    chunk_text: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processing_time: Mapped[Optional[float]] = mapped_column(Float)  # seconds
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Additional metadata
    embedding_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONEncodedDict)
    
    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="embeddings")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_embeddings_article_id', 'article_id'),
        Index('idx_embeddings_model', 'embedding_model'),
        Index('idx_embeddings_content_type', 'content_type'),
        Index('idx_embeddings_compound', 'article_id', 'content_type', 'embedding_model'),
        UniqueConstraint('article_id', 'content_type', 'embedding_model', 'chunk_index', 
                        name='uq_embeddings_article_content_model_chunk'),
    )


# Utility functions for JSON handling
def serialize_embedding(vector: List[float]) -> str:
    """Serialize embedding vector to JSON string."""
    return json.dumps(vector)


def deserialize_embedding(vector_str: str) -> List[float]:
    """Deserialize embedding vector from JSON string."""
    return json.loads(vector_str)
