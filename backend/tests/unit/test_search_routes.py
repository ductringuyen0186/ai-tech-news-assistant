"""
Unit Tests for Search API Routes
================================

Tests for search functionality API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from src.api.routes.search import router
from src.models.article import Article
from src.models.embedding import Embedding


class TestSearchRoutes:
    """Test cases for search routes."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with search routes."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies."""
        with patch('src.api.routes.search.get_article_repository') as mock_article_repo, \
             patch('src.api.routes.search.get_embedding_repository') as mock_embedding_repo, \
             patch('src.api.routes.search.get_embedding_service') as mock_embedding_service:
            
            yield {
                'article_repo': mock_article_repo.return_value,
                'embedding_repo': mock_embedding_repo.return_value,
                'embedding_service': mock_embedding_service.return_value
            }
    
    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        return [
            Article(
                id=1,
                title="AI Technology Advances",
                url="https://example.com/ai-tech",
                content="Artificial intelligence continues to advance rapidly...",
                author="John Doe",
                source="tech-news.com",
                categories=["AI", "Technology"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                view_count=10,
                embedding_generated=True
            ),
            Article(
                id=2,
                title="Machine Learning Breakthroughs",
                url="https://example.com/ml-breakthroughs",
                content="Recent breakthroughs in machine learning algorithms...",
                author="Jane Smith",
                source="ai-journal.com",
                categories=["Machine Learning", "Research"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                view_count=25,
                embedding_generated=True
            )
        ]
    
    def test_text_search_success(self, client, mock_dependencies, sample_articles):
        """Test successful text search."""
        mock_dependencies['article_repo'].search_articles.return_value = sample_articles
        
        response = client.get("/search/text?query=artificial intelligence&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_count" in data
        assert "query" in data
        assert "search_type" in data
        
        assert len(data["results"]) == 2
        assert data["query"] == "artificial intelligence"
        assert data["search_type"] == "text"
        
        # Verify repository was called with correct parameters
        mock_dependencies['article_repo'].search_articles.assert_called_once_with(
            "artificial intelligence", limit=10
        )
    
    def test_text_search_empty_query(self, client, mock_dependencies):
        """Test text search with empty query."""
        response = client.get("/search/text?query=")
        
        assert response.status_code == 400
        data = response.json()
        assert "Query cannot be empty" in data["detail"]
    
    def test_text_search_no_results(self, client, mock_dependencies):
        """Test text search with no results."""
        mock_dependencies['article_repo'].search_articles.return_value = []
        
        response = client.get("/search/text?query=nonexistent topic")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["results"] == []
        assert data["total_count"] == 0
        assert data["query"] == "nonexistent topic"
    
    def test_text_search_with_pagination(self, client, mock_dependencies, sample_articles):
        """Test text search with pagination parameters."""
        mock_dependencies['article_repo'].search_articles.return_value = sample_articles
        
        response = client.get("/search/text?query=AI&limit=5&offset=10")
        
        assert response.status_code == 200
        
        # Verify pagination parameters were passed
        mock_dependencies['article_repo'].search_articles.assert_called_once_with(
            "AI", limit=5, offset=10
        )
    
    def test_semantic_search_success(self, client, mock_dependencies, sample_articles):
        """Test successful semantic search."""
        # Mock embedding generation
        query_embedding = [0.1, 0.2, 0.3] * 100  # 300-dimensional vector
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            "embeddings": [query_embedding],
            "processing_time": 0.1
        }
        
        # Mock similarity search results
        similarity_results = [
            {
                "id": 1,
                "article_id": "article-1",
                "similarity_score": 0.95,
                "content_type": "article"
            },
            {
                "id": 2,
                "article_id": "article-2", 
                "similarity_score": 0.87,
                "content_type": "article"
            }
        ]
        mock_dependencies['embedding_repo'].search_similar.return_value = similarity_results
        
        # Mock article retrieval
        mock_dependencies['article_repo'].get_by_id.side_effect = lambda id: sample_articles[id-1]
        
        response = client.post("/search/semantic", json={
            "query": "artificial intelligence research",
            "limit": 10,
            "threshold": 0.7
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_count" in data
        assert "query" in data
        assert "search_type" in data
        assert "processing_time" in data
        
        assert len(data["results"]) == 2
        assert data["search_type"] == "semantic"
        assert data["results"][0]["similarity_score"] == 0.95
    
    def test_semantic_search_embedding_generation_failure(self, client, mock_dependencies):
        """Test semantic search when embedding generation fails."""
        mock_dependencies['embedding_service'].generate_embeddings.side_effect = Exception("Embedding failed")
        
        response = client.post("/search/semantic", json={
            "query": "test query",
            "limit": 10
        })
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate embeddings" in data["detail"]
    
    def test_semantic_search_no_similar_results(self, client, mock_dependencies):
        """Test semantic search with no similar results found."""
        # Mock embedding generation
        query_embedding = [0.1, 0.2, 0.3] * 100
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            "embeddings": [query_embedding],
            "processing_time": 0.1
        }
        
        # Mock empty similarity search results
        mock_dependencies['embedding_repo'].search_similar.return_value = []
        
        response = client.post("/search/semantic", json={
            "query": "very specific unmatched query",
            "limit": 10,
            "threshold": 0.9
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["results"] == []
        assert data["total_count"] == 0
    
    def test_semantic_search_with_content_type_filter(self, client, mock_dependencies):
        """Test semantic search with content type filter."""
        # Mock embedding generation
        query_embedding = [0.1, 0.2, 0.3] * 100
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            "embeddings": [query_embedding],
            "processing_time": 0.1
        }
        
        mock_dependencies['embedding_repo'].search_similar.return_value = []
        
        response = client.post("/search/semantic", json={
            "query": "test query",
            "limit": 10,
            "content_type": "summary"
        })
        
        assert response.status_code == 200
        
        # Verify content type filter was applied
        mock_dependencies['embedding_repo'].search_similar.assert_called_once()
        call_args = mock_dependencies['embedding_repo'].search_similar.call_args
        assert call_args[1]['content_type'] == "summary"
    
    def test_hybrid_search_success(self, client, mock_dependencies, sample_articles):
        """Test successful hybrid search."""
        # Mock text search results
        mock_dependencies['article_repo'].search_articles.return_value = sample_articles
        
        # Mock semantic search setup
        query_embedding = [0.1, 0.2, 0.3] * 100
        mock_dependencies['embedding_service'].generate_embeddings.return_value = {
            "embeddings": [query_embedding],
            "processing_time": 0.1
        }
        
        similarity_results = [
            {
                "id": 1,
                "article_id": "article-1",
                "similarity_score": 0.95,
                "content_type": "article"
            }
        ]
        mock_dependencies['embedding_repo'].search_similar.return_value = similarity_results
        mock_dependencies['article_repo'].get_by_id.return_value = sample_articles[0]
        
        response = client.post("/search/hybrid", json={
            "query": "artificial intelligence",
            "limit": 10,
            "text_weight": 0.6,
            "semantic_weight": 0.4
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "search_type" in data
        assert data["search_type"] == "hybrid"
        assert "text_results_count" in data
        assert "semantic_results_count" in data
    
    def test_hybrid_search_weights_validation(self, client, mock_dependencies):
        """Test hybrid search weight validation."""
        # Test weights that don't sum to 1.0
        response = client.post("/search/hybrid", json={
            "query": "test",
            "text_weight": 0.3,
            "semantic_weight": 0.4  # Sum = 0.7, not 1.0
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "Weights must sum to 1.0" in data["detail"]
    
    def test_get_search_suggestions_success(self, client, mock_dependencies):
        """Test getting search suggestions."""
        # Mock popular search terms or categories
        mock_suggestions = [
            {"term": "artificial intelligence", "count": 150},
            {"term": "machine learning", "count": 120},
            {"term": "deep learning", "count": 80}
        ]
        
        mock_dependencies['article_repo'].get_popular_search_terms.return_value = mock_suggestions
        
        response = client.get("/search/suggestions?query=arti")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        assert any("artificial intelligence" in suggestion["term"] for suggestion in data["suggestions"])
    
    def test_get_trending_searches(self, client, mock_dependencies):
        """Test getting trending searches."""
        mock_trending = [
            {"query": "ChatGPT updates", "search_count": 500, "trend_score": 95},
            {"query": "AI ethics", "search_count": 300, "trend_score": 88},
            {"query": "neural networks", "search_count": 250, "trend_score": 75}
        ]
        
        mock_dependencies['article_repo'].get_trending_searches.return_value = mock_trending
        
        response = client.get("/search/trending")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trending" in data
        assert len(data["trending"]) == 3
        assert data["trending"][0]["query"] == "ChatGPT updates"
    
    def test_search_analytics(self, client, mock_dependencies):
        """Test search analytics endpoint."""
        mock_analytics = {
            "total_searches": 10000,
            "unique_queries": 2500,
            "avg_results_per_search": 8.5,
            "popular_categories": ["AI", "Technology", "Research"],
            "search_success_rate": 0.87
        }
        
        mock_dependencies['article_repo'].get_search_analytics.return_value = mock_analytics
        
        response = client.get("/search/analytics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_searches" in data
        assert "unique_queries" in data
        assert "avg_results_per_search" in data
        assert data["search_success_rate"] == 0.87
    
    def test_advanced_search_with_filters(self, client, mock_dependencies, sample_articles):
        """Test advanced search with multiple filters."""
        mock_dependencies['article_repo'].advanced_search.return_value = (sample_articles, 2)
        
        response = client.post("/search/advanced", json={
            "query": "artificial intelligence",
            "filters": {
                "author": "John Doe",
                "source": "tech-news.com",
                "categories": ["AI", "Technology"],
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
                "min_views": 5
            },
            "sort_by": "relevance",
            "sort_order": "desc",
            "limit": 20,
            "offset": 0
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_count" in data
        assert "filters_applied" in data
        assert len(data["results"]) == 2
        
        # Verify advanced search was called with correct parameters
        mock_dependencies['article_repo'].advanced_search.assert_called_once()
    
    def test_search_export(self, client, mock_dependencies, sample_articles):
        """Test search results export functionality."""
        mock_dependencies['article_repo'].search_articles.return_value = sample_articles
        
        response = client.get("/search/export?query=AI&format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers["content-disposition"]
        
        # Verify CSV content
        csv_content = response.content.decode()
        assert "title,url,author,source" in csv_content
        assert "AI Technology Advances" in csv_content
    
    def test_search_export_json_format(self, client, mock_dependencies, sample_articles):
        """Test search results export in JSON format."""
        mock_dependencies['article_repo'].search_articles.return_value = sample_articles
        
        response = client.get("/search/export?query=AI&format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2


class TestSearchValidation:
    """Test search input validation and error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_text_search_query_too_long(self, client):
        """Test text search with query that is too long."""
        long_query = "a" * 1000  # 1000 character query
        
        response = client.get(f"/search/text?query={long_query}")
        
        assert response.status_code == 400
        data = response.json()
        assert "Query too long" in data["detail"]
    
    def test_semantic_search_invalid_threshold(self, client):
        """Test semantic search with invalid threshold."""
        response = client.post("/search/semantic", json={
            "query": "test",
            "threshold": 1.5  # Invalid threshold > 1.0
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_semantic_search_invalid_limit(self, client):
        """Test semantic search with invalid limit."""
        response = client.post("/search/semantic", json={
            "query": "test",
            "limit": -1  # Invalid negative limit
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_hybrid_search_missing_query(self, client):
        """Test hybrid search with missing query."""
        response = client.post("/search/hybrid", json={
            "limit": 10,
            "text_weight": 0.5,
            "semantic_weight": 0.5
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_advanced_search_invalid_date_range(self, client):
        """Test advanced search with invalid date range."""
        response = client.post("/search/advanced", json={
            "query": "test",
            "filters": {
                "date_from": "2024-12-31",
                "date_to": "2024-01-01"  # End date before start date
            }
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid date range" in data["detail"]


class TestSearchPerformance:
    """Test search performance and optimization."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @patch('src.api.routes.search.get_article_repository')
    def test_search_caching(self, mock_article_repo, client):
        """Test search result caching."""
        mock_repo = mock_article_repo.return_value
        mock_repo.search_articles.return_value = []
        
        # First search
        response1 = client.get("/search/text?query=test&limit=10")
        assert response1.status_code == 200
        
        # Second identical search - should use cache
        response2 = client.get("/search/text?query=test&limit=10")
        assert response2.status_code == 200
        
        # Verify repository was called only once (due to caching)
        assert mock_repo.search_articles.call_count == 1
    
    @patch('src.api.routes.search.get_article_repository')
    def test_search_pagination_performance(self, mock_article_repo, client):
        """Test search pagination performance."""
        mock_repo = mock_article_repo.return_value
        mock_repo.search_articles.return_value = []
        
        # Test large offset
        response = client.get("/search/text?query=test&limit=10&offset=1000")
        
        assert response.status_code == 200
        
        # Verify repository was called with correct offset
        mock_repo.search_articles.assert_called_once_with(
            "test", limit=10, offset=1000
        )
    
    @patch('src.api.routes.search.get_embedding_service')
    @patch('src.api.routes.search.get_embedding_repository')
    def test_semantic_search_batch_processing(self, mock_embedding_repo, mock_embedding_service, client):
        """Test semantic search with batch processing optimization."""
        # Mock embedding service
        mock_service = mock_embedding_service.return_value
        mock_service.generate_embeddings.return_value = {
            "embeddings": [[0.1] * 300],
            "processing_time": 0.05
        }
        
        # Mock repository
        mock_repo = mock_embedding_repo.return_value
        mock_repo.search_similar.return_value = []
        
        response = client.post("/search/semantic", json={
            "query": "test query for batch processing",
            "limit": 100  # Large limit to test batch processing
        })
        
        assert response.status_code == 200
        
        # Verify embeddings were generated efficiently
        mock_service.generate_embeddings.assert_called_once()
        mock_repo.search_similar.assert_called_once()
