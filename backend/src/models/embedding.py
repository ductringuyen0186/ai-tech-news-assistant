"""
Embedding Data Models
====================

Pydantic models for embedding-related data structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EmbeddingBase(BaseModel):
    """Base embedding model."""
    model_name: str = Field(..., description="Name of the embedding model")
    embedding_dim: int = Field(..., gt=0, description="Dimension of the embedding vector")


class EmbeddingRequest(BaseModel):
    """Model for embedding generation requests."""
    texts: List[str] = Field(..., min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, description="Override default model")
    normalize: bool = Field(True, description="Whether to normalize embeddings")
    batch_size: int = Field(32, ge=1, le=128, description="Batch size for processing")


class EmbeddingResponse(BaseModel):
    """Model for embedding generation responses."""
    embeddings: List[List[float]] = Field(..., description="Generated embedding vectors")
    model_name: str = Field(..., description="Model used for generation")
    embedding_dim: int = Field(..., description="Dimension of embeddings")
    processing_time: float = Field(..., description="Time taken for generation in seconds")


class EmbeddingStats(BaseModel):
    """Model for embedding statistics."""
    total_embeddings: int = Field(0, description="Total number of embeddings")
    models_used: Dict[str, int] = Field(default_factory=dict, description="Count by model")
    average_dimension: float = Field(0.0, description="Average embedding dimension")
    storage_size_mb: float = Field(0.0, description="Estimated storage size in MB")


class SimilarityRequest(BaseModel):
    """Model for similarity computation requests."""
    query_text: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=50, description="Number of similar items to return")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    include_metadata: bool = Field(True, description="Whether to include metadata")


class SimilarityResult(BaseModel):
    """Model for similarity search results."""
    id: str = Field(..., description="Identifier of the similar item")
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Associated metadata")
    content_snippet: Optional[str] = Field(None, description="Content preview")


class EmbeddingCreate(BaseModel):
    """Model for creating new embeddings."""
    text: str = Field(..., min_length=1, max_length=10000)
    model_name: Optional[str] = Field(None, description="Model to use for embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EmbeddingUpdate(BaseModel):
    """Model for updating existing embeddings."""
    text: Optional[str] = Field(None, min_length=1, max_length=10000)
    model_name: Optional[str] = Field(None, description="Model name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class Embedding(BaseModel):
    """Complete embedding model."""
    id: str = Field(..., description="Unique embedding identifier")
    text: str = Field(..., description="Source text")
    vector: List[float] = Field(..., description="Embedding vector")
    model_name: str = Field(..., description="Model used for generation")
    embedding_dim: int = Field(..., description="Vector dimension")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class EmbeddingSearchRequest(BaseModel):
    """Model for embedding search requests."""
    query_text: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class EmbeddingError(BaseModel):
    """Model for embedding-related errors."""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
