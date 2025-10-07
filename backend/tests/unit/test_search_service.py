"""
Unit Tests for SearchService
============================

Comprehensive tests for the semantic search service including:
- Embedding generation
- Vector similarity search
- Result reranking
- Health checks
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import numpy as np

from src.services.search_service import SearchService, get_search_service
from src.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchHealthResponse
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_embedding_generator():
    """Mock EmbeddingGenerator for testing."""
    generator = Mock()
    generator.generate_embeddings = AsyncMock()
    generator.model_name = "all-MiniLM-L6-v2"
    generator.embedding_dim = 384
    return generator


@pytest.fixture
def mock_db_connection():
    """Mock SQLite database connection."""
    conn = Mock()
    cursor = Mock()
    conn.cursor.return_value = cursor
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    return conn


@pytest.fixture
def search_service(mock_embedding_generator, mock_db_connection):
    """Create SearchService instance with mocked dependencies."""
    with patch('src.services.search_service.EmbeddingGenerator', return_value=mock_embedding_generator):
        with patch('sqlite3.connect', return_value=mock_db_connection):
            service = SearchService()
            service.embedding_generator = mock_embedding_generator
            service.db_path = ":memory:"
            return service


@pytest.fixture
def sample_search_request():
    """Sample search request for testing."""
    return SearchRequest(
        query="artificial intelligence breakthroughs",
        limit=10,
        min_score=0.5,
        use_reranking=True
    )


@pytest.fixture
def sample_embedding():
    """Sample embedding vector (384 dimensions)."""
    return np.random.rand(384).tolist()


@pytest.fixture
def sample_db_results():
    """Sample database results from vector search."""
    base_time = datetime.now()
    return [
        (
            "article_1",
            "New AI Model Achieves Human-Level Performance",
            "https://example.com/article1",
            "hackernews",
            ["AI", "Machine Learning"],
            ["neural networks", "deep learning"],
            (base_time - timedelta(days=1)).isoformat(),
            0.85,
            "article_1_embedding"
        ),
        (
            "article_2",
            "Breakthrough in Natural Language Processing",
            "https://example.com/article2",
            "techcrunch",
            ["NLP", "AI"],
            ["transformers", "language models"],
            (base_time - timedelta(days=2)).isoformat(),
            0.78,
            "article_2_embedding"
        ),
        (
            "article_3",
            "AI Ethics and Responsible Development",
            "https://example.com/article3",
            "reddit",
            ["AI", "Ethics"],
            ["fairness", "bias"],
            (base_time - timedelta(days=5)).isoformat(),
            0.62,
            "article_3_embedding"
        )
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

class TestSearchServiceInitialization:
    """Test SearchService initialization and setup."""
    
    def test_initialization_success(self, search_service):
        """Test successful service initialization."""
        assert search_service is not None
        assert search_service.embedding_generator is not None
        assert search_service.db_path is not None
    
    def test_singleton_pattern(self):
        """Test that get_search_service returns the same instance."""
        with patch('src.services.search_service.SearchService') as MockService:
            get_search_service()
            get_search_service()
            
            # Should only create one instance
            assert MockService.call_count == 1


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheck:
    """Test search service health check functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, search_service, mock_db_connection):
        """Test successful health check."""
        # Mock database query for article count
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchone.return_value = (150,)  # 150 articles indexed
        
        health = await search_service.health_check()
        
        assert isinstance(health, SearchHealthResponse)
        assert health.status == "healthy"
        assert health.total_indexed_articles == 150
        assert health.embedding_dimensions == 384
        assert health.model_name == "all-MiniLM-L6-v2"
    
    @pytest.mark.asyncio
    async def test_health_check_no_articles(self, search_service, mock_db_connection):
        """Test health check when no articles are indexed."""
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchone.return_value = (0,)
        
        health = await search_service.health_check()
        
        assert health.status == "degraded"
        assert health.total_indexed_articles == 0
    
    @pytest.mark.asyncio
    async def test_health_check_database_error(self, search_service, mock_db_connection):
        """Test health check handles database errors."""
        cursor = mock_db_connection.cursor.return_value
        cursor.execute.side_effect = Exception("Database connection failed")
        
        health = await search_service.health_check()
        
        assert health.status == "unhealthy"


# ============================================================================
# Embedding Generation Tests
# ============================================================================

class TestEmbeddingGeneration:
    """Test query embedding generation."""
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_success(
        self, 
        search_service, 
        sample_embedding
    ):
        """Test successful query embedding generation."""
        query = "machine learning algorithms"
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        
        embedding = await search_service._generate_query_embedding(query)
        
        assert embedding is not None
        assert len(embedding) == 384
        search_service.embedding_generator.generate_embeddings.assert_called_once_with([query])
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_empty_query(self, search_service):
        """Test embedding generation with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_service._generate_query_embedding("")
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_error(self, search_service):
        """Test embedding generation error handling."""
        search_service.embedding_generator.generate_embeddings.side_effect = Exception("Model error")
        
        with pytest.raises(Exception, match="Model error"):
            await search_service._generate_query_embedding("test query")


# ============================================================================
# Vector Search Tests
# ============================================================================

class TestVectorSearch:
    """Test vector similarity search functionality."""
    
    @pytest.mark.asyncio
    async def test_vector_search_success(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test successful vector search."""
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        results = await search_service._vector_search(
            query_embedding=sample_embedding,
            request=sample_search_request
        )
        
        assert len(results) > 0
        assert all(isinstance(r, SearchResultItem) for r in results)
        assert results[0].score >= results[-1].score  # Sorted by score
    
    @pytest.mark.asyncio
    async def test_vector_search_with_source_filter(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test vector search with source filtering."""
        sample_search_request.sources = ["hackernews"]
        cursor = mock_db_connection.cursor.return_value
        
        # Filter results to only hackernews
        filtered_results = [r for r in sample_db_results if r[3] == "hackernews"]
        cursor.fetchall.return_value = filtered_results
        
        results = await search_service._vector_search(
            query_embedding=sample_embedding,
            request=sample_search_request
        )
        
        assert all(r.source == "hackernews" for r in results)
    
    @pytest.mark.asyncio
    async def test_vector_search_with_category_filter(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test vector search with category filtering."""
        sample_search_request.categories = ["AI"]
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        results = await search_service._vector_search(
            query_embedding=sample_embedding,
            request=sample_search_request
        )
        
        # Should only return articles with "AI" category
        assert all("AI" in r.categories for r in results)
    
    @pytest.mark.asyncio
    async def test_vector_search_min_score_filter(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test vector search respects minimum score threshold."""
        sample_search_request.min_score = 0.75
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        results = await search_service._vector_search(
            query_embedding=sample_embedding,
            request=sample_search_request
        )
        
        assert all(r.score >= 0.75 for r in results)
    
    @pytest.mark.asyncio
    async def test_vector_search_no_results(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        mock_db_connection
    ):
        """Test vector search with no matching results."""
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = []
        
        results = await search_service._vector_search(
            query_embedding=sample_embedding,
            request=sample_search_request
        )
        
        assert len(results) == 0


# ============================================================================
# Reranking Tests
# ============================================================================

class TestReranking:
    """Test result reranking functionality."""
    
    @pytest.mark.asyncio
    async def test_rerank_results_improves_relevance(
        self,
        search_service,
        sample_search_request
    ):
        """Test that reranking improves relevance ordering."""
        base_time = datetime.now()
        
        # Create results with different characteristics
        results = [
            SearchResultItem(
                article_id="old_exact_match",
                title="artificial intelligence breakthroughs",  # Exact title match
                url="https://example.com/1",
                source="hackernews",
                categories=["AI"],
                keywords=["AI"],
                published_date=(base_time - timedelta(days=30)).isoformat(),
                score=0.60,  # Lower vector score
                embedding_id="emb_1"
            ),
            SearchResultItem(
                article_id="recent_partial_match",
                title="Recent AI Research Updates",
                url="https://example.com/2",
                source="techcrunch",
                categories=["AI"],
                keywords=["AI"],
                published_date=(base_time - timedelta(days=1)).isoformat(),
                score=0.75,  # Higher vector score
                embedding_id="emb_2"
            ),
            SearchResultItem(
                article_id="old_no_match",
                title="Technology News Roundup",
                url="https://example.com/3",
                source="reddit",
                categories=["Tech"],
                keywords=["tech"],
                published_date=(base_time - timedelta(days=60)).isoformat(),
                score=0.55,  # Lowest vector score
                embedding_id="emb_3"
            )
        ]
        
        reranked = await search_service._rerank_results(
            results=results,
            query="artificial intelligence breakthroughs"
        )
        
        assert len(reranked) == len(results)
        # Reranked scores should differ from original
        assert reranked[0].score != results[0].score
        # Should still be sorted by score
        assert reranked[0].score >= reranked[1].score >= reranked[2].score
    
    @pytest.mark.asyncio
    async def test_rerank_title_matching_boost(
        self,
        search_service
    ):
        """Test that exact title matches get boosted in reranking."""
        query = "machine learning"
        
        results = [
            SearchResultItem(
                article_id="exact_match",
                title="Machine Learning Tutorial",  # Exact match
                url="https://example.com/1",
                source="hackernews",
                categories=["AI"],
                keywords=["ML"],
                published_date=datetime.now().isoformat(),
                score=0.60,
                embedding_id="emb_1"
            ),
            SearchResultItem(
                article_id="no_match",
                title="Data Science Overview",  # No match
                url="https://example.com/2",
                source="techcrunch",
                categories=["Data"],
                keywords=["data"],
                published_date=datetime.now().isoformat(),
                score=0.65,
                embedding_id="emb_2"
            )
        ]
        
        reranked = await search_service._rerank_results(results, query)
        
        # Exact match should be ranked higher despite lower original score
        assert reranked[0].article_id == "exact_match"
    
    @pytest.mark.asyncio
    async def test_rerank_recency_boost(
        self,
        search_service
    ):
        """Test that recent articles get boosted in reranking."""
        base_time = datetime.now()
        
        results = [
            SearchResultItem(
                article_id="old_article",
                title="AI Research",
                url="https://example.com/1",
                source="hackernews",
                categories=["AI"],
                keywords=["AI"],
                published_date=(base_time - timedelta(days=365)).isoformat(),
                score=0.70,
                embedding_id="emb_1"
            ),
            SearchResultItem(
                article_id="recent_article",
                title="AI Research",
                url="https://example.com/2",
                source="techcrunch",
                categories=["AI"],
                keywords=["AI"],
                published_date=(base_time - timedelta(days=1)).isoformat(),
                score=0.65,  # Slightly lower score
                embedding_id="emb_2"
            )
        ]
        
        reranked = await search_service._rerank_results(results, "AI")
        
        # Recent article should be ranked higher due to recency boost
        assert reranked[0].article_id == "recent_article"


# ============================================================================
# Full Search Flow Tests
# ============================================================================

class TestSearchFlow:
    """Test complete search flow from request to response."""
    
    @pytest.mark.asyncio
    async def test_search_complete_flow(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test complete search flow with all components."""
        # Mock embedding generation
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        
        # Mock database results
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        response = await search_service.search(sample_search_request)
        
        assert isinstance(response, SearchResponse)
        assert response.query == sample_search_request.query
        assert response.total_results > 0
        assert len(response.results) > 0
        assert response.execution_time_ms > 0
        assert all(isinstance(r, SearchResultItem) for r in response.results)
    
    @pytest.mark.asyncio
    async def test_search_with_reranking(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test search with reranking enabled."""
        sample_search_request.use_reranking = True
        
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        response = await search_service.search(sample_search_request)
        
        assert response.reranking_applied is True
    
    @pytest.mark.asyncio
    async def test_search_without_reranking(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test search without reranking."""
        sample_search_request.use_reranking = False
        
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        response = await search_service.search(sample_search_request)
        
        assert response.reranking_applied is False
    
    @pytest.mark.asyncio
    async def test_search_respects_limit(
        self,
        search_service,
        sample_embedding,
        mock_db_connection
    ):
        """Test that search respects result limit."""
        # Create request with small limit
        request = SearchRequest(query="test", limit=2)
        
        # Mock many results
        many_results = sample_db_results * 10  # 30 results
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = many_results
        
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        
        response = await search_service.search(request)
        
        assert len(response.results) <= 2


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in search operations."""
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_service):
        """Test search with empty query."""
        request = SearchRequest(query="", limit=10)
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await search_service.search(request)
    
    @pytest.mark.asyncio
    async def test_search_database_error(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        mock_db_connection
    ):
        """Test search handles database errors."""
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        
        cursor = mock_db_connection.cursor.return_value
        cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await search_service.search(sample_search_request)
    
    @pytest.mark.asyncio
    async def test_search_embedding_error(
        self,
        search_service,
        sample_search_request
    ):
        """Test search handles embedding generation errors."""
        search_service.embedding_generator.generate_embeddings.side_effect = Exception("Embedding error")
        
        with pytest.raises(Exception, match="Embedding error"):
            await search_service.search(sample_search_request)


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics of search."""
    
    @pytest.mark.asyncio
    async def test_search_execution_time_recorded(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        sample_db_results,
        mock_db_connection
    ):
        """Test that execution time is recorded."""
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = sample_db_results
        
        response = await search_service.search(sample_search_request)
        
        assert response.execution_time_ms > 0
        assert isinstance(response.execution_time_ms, (int, float))
    
    @pytest.mark.asyncio
    async def test_search_handles_large_result_sets(
        self,
        search_service,
        sample_search_request,
        sample_embedding,
        mock_db_connection
    ):
        """Test search handles large result sets efficiently."""
        # Create 1000 mock results
        large_result_set = []
        for i in range(1000):
            large_result_set.append((
                f"article_{i}",
                f"Title {i}",
                f"https://example.com/{i}",
                "hackernews",
                ["AI"],
                ["keyword"],
                datetime.now().isoformat(),
                0.7,
                f"emb_{i}"
            ))
        
        search_service.embedding_generator.generate_embeddings.return_value = np.array([sample_embedding])
        cursor = mock_db_connection.cursor.return_value
        cursor.fetchall.return_value = large_result_set
        
        sample_search_request.limit = 50
        response = await search_service.search(sample_search_request)
        
        assert len(response.results) == 50
        assert response.total_results == 1000
