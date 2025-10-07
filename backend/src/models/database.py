"""
Database Data Models
==================

Pydantic models for database operations and responses.
"""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Model for database health check."""
    status: str = Field(..., description="Database status")
    connection_pool_size: Optional[int] = Field(None, description="Connection pool size")
    active_connections: Optional[int] = Field(None, description="Active connections")
    last_migration: Optional[datetime] = Field(None, description="Last migration timestamp")


class DatabaseStats(BaseModel):
    """Model for database statistics."""
    total_articles: int = Field(0, description="Total number of articles")
    total_embeddings: int = Field(0, description="Total number of embeddings")
    database_size_mb: float = Field(0.0, description="Database size in MB")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    table_stats: Dict[str, int] = Field(default_factory=dict, description="Row counts by table")
    # Additional fields for comprehensive stats
    articles_today: Optional[int] = Field(None, description="Articles added today")
    unique_sources: Optional[int] = Field(None, description="Number of unique sources")
    avg_articles_per_day: Optional[float] = Field(None, description="Average articles per day")
    articles_with_summaries: Optional[int] = Field(None, description="Articles with summaries")
    articles_with_embeddings: Optional[int] = Field(None, description="Articles with embeddings")


class QueryResult(BaseModel):
    """Generic model for query results."""
    success: bool = Field(..., description="Whether the query was successful")
    affected_rows: int = Field(0, description="Number of affected rows")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if query failed")


class BulkOperation(BaseModel):
    """Model for bulk database operations."""
    operation_type: str = Field(..., description="Type of bulk operation")
    total_items: int = Field(..., ge=1, description="Total number of items to process")
    batch_size: int = Field(100, ge=1, le=1000, description="Items per batch")
    parallel_workers: int = Field(1, ge=1, le=10, description="Number of parallel workers")


class BulkOperationResult(BaseModel):
    """Model for bulk operation results."""
    operation_id: str = Field(..., description="Unique operation identifier")
    status: str = Field(..., description="Operation status")
    processed_items: int = Field(0, description="Number of processed items")
    failed_items: int = Field(0, description="Number of failed items")
    total_time_seconds: float = Field(..., description="Total operation time")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
