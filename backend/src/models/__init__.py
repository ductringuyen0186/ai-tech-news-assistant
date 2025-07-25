"""
Data Models Package
=================

Centralized data models for the AI Tech News Assistant.
Provides type-safe data structures for API operations, database interactions,
and business logic.
"""

from .article import (
    Article,
    ArticleCreate,
    ArticleUpdate,
    ArticleSummary,
    ArticleStats,
    ArticleSearchRequest,
    ArticleSearchResult,
    SummarizationRequest
)

from .embedding import (
    EmbeddingBase,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingStats,
    SimilarityRequest,
    SimilarityResult,
    EmbeddingCreate,
    EmbeddingUpdate,
    Embedding,
    EmbeddingSearchRequest,
    EmbeddingError
)

from .database import (
    DatabaseHealth,
    DatabaseStats,
    QueryResult,
    BulkOperation,
    BulkOperationResult
)

from .api import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    HealthCheck,
    HealthResponse,
    ComponentHealth,
    AsyncTaskResponse
)

__all__ = [
    # Article models
    "Article",
    "ArticleCreate", 
    "ArticleUpdate",
    "ArticleSummary",
    "ArticleStats",
    "ArticleSearchRequest",
    "ArticleSearchResult",
    "SummarizationRequest",
    
    # Embedding models
    "EmbeddingBase",
    "EmbeddingRequest",
    "EmbeddingResponse", 
    "EmbeddingStats",
    "EmbeddingCreate",
    "EmbeddingUpdate",
    "Embedding",
    "EmbeddingSearchRequest",
    "EmbeddingError",
    "SimilarityRequest",
    "SimilarityResult",
    
    # Database models
    "DatabaseHealth",
    "DatabaseStats",
    "QueryResult",
    "BulkOperation",
    "BulkOperationResult",
    
    # API models
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "HealthCheck",
    "HealthResponse",
    "ComponentHealth",
    "AsyncTaskResponse"
]
