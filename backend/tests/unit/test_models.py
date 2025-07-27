"""
Model Tests
===========

Tests for Pydantic models to boost coverage.
"""

import pytest
from datetime import datetime
from src.models.api import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    HealthCheck,
    AsyncTaskResponse
)
from src.models.article import (
    ArticleBase,
    ArticleCreate,
    ArticleUpdate,
    Article,
    ArticleSummary,
    ArticleStats,
    ArticleSearchRequest,
    ArticleSearchResult,
    SummarizationRequest
)
from src.models.embedding import (
    EmbeddingBase,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingStats,
    SimilarityRequest,
    SimilarityResult
)
from src.models.database import (
    DatabaseHealth,
    DatabaseStats,
    QueryResult
)


class TestApiModels:
    """Test API response models."""
    
    def test_base_response(self):
        """Test BaseResponse model."""
        response = BaseResponse[str](
            success=True,
            message="Success",
            data="test data"
        )
        assert response.success is True
        assert response.message == "Success"
        assert response.data == "test data"
        assert isinstance(response.timestamp, datetime)
        
    def test_error_detail(self):
        """Test ErrorDetail model."""
        detail = ErrorDetail(
            error_code="VAL001",
            error_type="validation",
            field="email",
            message="Invalid email format"
        )
        assert detail.error_code == "VAL001"
        assert detail.error_type == "validation"
        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        
    def test_error_response(self):
        """Test ErrorResponse model."""
        response = ErrorResponse(
            error_code="ERR001",
            error_type="system",
            message="System error"
        )
        assert response.success is False
        assert response.error_code == "ERR001"
        assert response.error_type == "system"
        assert response.message == "System error"
        assert isinstance(response.timestamp, datetime)
        
    def test_pagination_info(self):
        """Test PaginationInfo model."""
        pagination = PaginationInfo(
            page=1,
            page_size=10,
            total_items=100,
            total_pages=10,
            has_next=True,
            has_previous=False
        )
        assert pagination.page == 1
        assert pagination.page_size == 10
        assert pagination.total_items == 100
        assert pagination.total_pages == 10
        assert pagination.has_next is True
        assert pagination.has_previous is False
        
    def test_health_check(self):
        """Test HealthCheck model."""
        health = HealthCheck(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.0,
            dependencies={"database": "healthy", "redis": "healthy"}
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.uptime_seconds == 3600.0
        assert health.dependencies["database"] == "healthy"


class TestArticleModels:
    """Test article-related models."""
    
    def test_article_create(self):
        """Test ArticleCreate model."""
        article = ArticleCreate(
            title="Test Article",
            url="https://example.com/article",
            content="Test content for the article",
            author="Test Author",
            source="example.com"
        )
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.content == "Test content for the article"
        assert article.author == "Test Author"
        assert article.source == "example.com"
        
    def test_article_summary(self):
        """Test ArticleSummary model."""
        from datetime import datetime, timezone
        summary = ArticleSummary(
            id=1,
            title="Test Article",
            summary="This is a test summary",
            source="example.com",
            published_date=datetime.now(timezone.utc),
            url="https://example.com/article"
        )
        assert summary.id == 1
        assert summary.title == "Test Article"
        assert summary.summary == "This is a test summary"
        assert summary.source == "example.com"
        assert summary.url == "https://example.com/article"
        
    def test_summarization_request(self):
        """Test SummarizationRequest model."""
        request = SummarizationRequest(
            content="Long article content to summarize",
            max_length=100,
            style="concise"
        )
        assert request.content == "Long article content to summarize"
        assert request.max_length == 100
        assert request.style == "concise"
        
    def test_article_search_request(self):
        """Test ArticleSearchRequest model."""
        search = ArticleSearchRequest(
            query="AI technology",
            limit=10,
            source="techcrunch.com"
        )
        assert search.query == "AI technology"
        assert search.limit == 10
        assert search.source == "techcrunch.com"
        assert search.similarity_threshold == 0.7  # default value


class TestEmbeddingModels:
    """Test embedding-related models."""
    
    def test_embedding_request(self):
        """Test EmbeddingRequest model."""
        request = EmbeddingRequest(
            texts=["Text 1", "Text 2"],
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            normalize=True,
            batch_size=32
        )
        assert request.texts == ["Text 1", "Text 2"]
        assert request.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert request.normalize is True
        assert request.batch_size == 32
        
    def test_embedding_response(self):
        """Test EmbeddingResponse model."""
        response = EmbeddingResponse(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            model_name="test-model",
            embedding_dim=3,
            processing_time=0.5
        )
        assert response.embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        assert response.model_name == "test-model"
        assert response.embedding_dim == 3
        assert response.processing_time == 0.5
        
    def test_similarity_request(self):
        """Test SimilarityRequest model."""
        request = SimilarityRequest(
            query_text="Find similar content",
            top_k=10,
            similarity_threshold=0.8,
            include_metadata=True
        )
        assert request.query_text == "Find similar content"
        assert request.top_k == 10
        assert request.similarity_threshold == 0.8
        assert request.include_metadata is True
        
    def test_similarity_result(self):
        """Test SimilarityResult model."""
        result = SimilarityResult(
            id="article-123",
            similarity_score=0.85,
            metadata={"title": "Test Article"},
            content_snippet="This is a snippet..."
        )
        assert result.id == "article-123"
        assert result.similarity_score == 0.85
        assert result.metadata == {"title": "Test Article"}
        assert result.content_snippet == "This is a snippet..."


class TestDatabaseModels:
    """Test database-related models."""
    
    def test_database_health(self):
        """Test DatabaseHealth model."""
        health = DatabaseHealth(
            status="healthy",
            connection_pool_size=10,
            active_connections=3
        )
        assert health.status == "healthy"
        assert health.connection_pool_size == 10
        assert health.active_connections == 3
        
    def test_database_stats(self):
        """Test DatabaseStats model."""
        stats = DatabaseStats(
            total_articles=100,
            total_embeddings=50,
            database_size_mb=25.5,
            table_stats={"articles": 100, "embeddings": 50}
        )
        assert stats.total_articles == 100
        assert stats.total_embeddings == 50
        assert stats.database_size_mb == 25.5
        assert stats.table_stats == {"articles": 100, "embeddings": 50}
        assert isinstance(stats.last_updated, datetime)
