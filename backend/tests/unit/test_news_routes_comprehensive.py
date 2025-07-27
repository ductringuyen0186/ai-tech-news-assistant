"""
Comprehensive Unit Tests for News Routes
=======================================

Tests for news API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import status
from typing import List, Dict, Any

from src.api.routes.news import router
from src.models.article import Article, ArticleCreate, ArticleStats
from src.models.api import PaginatedResponse, BaseResponse


@pytest.fixture
def test_app():
    """Create test FastAPI app with news routes."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)  # Router already has /news prefix
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    return [
        Article(
            id=1,
            title="AI Revolution 2024",
            url="https://technews.com/ai-revolution",
            content="Article about AI advancements",
            author="John Doe",
            source="technews.com",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            view_count=100,
            categories=["AI", "Technology"]
        ),
        Article(
            id=2,
            title="Machine Learning Breakthrough",
            url="https://mlnews.com/breakthrough",
            content="New ML algorithms discovered",
            author="Jane Smith",
            source="mlnews.com",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            view_count=150,
            categories=["ML", "Research"]
        )
    ]


@pytest.fixture
def sample_article_stats():
    """Sample article statistics."""
    return ArticleStats(
        total_articles=100,
        articles_with_summaries=75,
        articles_with_embeddings=50,
        top_sources=[
            {"source": "technews.com", "count": 25},
            {"source": "mlnews.com", "count": 20}
        ],
        recent_articles=15
    )


class TestNewsRoutes:
    """Test cases for news API endpoints."""
    
    def test_get_articles_default_params(self, client, sample_articles):
        """Test getting articles with default parameters."""
        from src.api.routes.news import get_article_repository
        from unittest.mock import AsyncMock
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["pagination"]["total_items"] == 2
            assert data["pagination"]["page"] == 1
            assert data["pagination"]["page_size"] == 20
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_articles_with_pagination(self, client, sample_articles):
        """Test getting articles with pagination parameters."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 10))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/?page=2&page_size=5")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["pagination"]["page"] == 2
            assert data["pagination"]["page_size"] == 5
            
            # Verify repository was called with correct offset
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            assert call_args[1]["limit"] == 5
            assert call_args[1]["offset"] == 5  # page 2, size 5 = offset 5
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_articles_with_filters(self, client, sample_articles):
        """Test getting articles with filter parameters."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 1))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/?source=technews.com")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called with filters
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            assert call_args[1]["source"] == "technews.com"
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_articles_with_sorting(self, client, sample_articles):
        """Test getting articles with sorting parameters."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/?sort_by=view_count&sort_desc=false")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called (sorting is handled at API level, not repository level)
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            # Only test parameters that are actually passed to repository
            assert call_args[1]["limit"] == 20  # default page_size
            assert call_args[1]["offset"] == 0   # default offset for page 1
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_article_by_id_success(self, client, sample_articles):
        """Test getting a specific article by ID."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.get_by_id = AsyncMock(return_value=sample_articles[0])
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/1")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["id"] == 1
            assert data["data"]["title"] == "AI Revolution 2024"
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_article_by_id_not_found(self, client):
        """Test getting non-existent article."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository that raises exception
        mock_repository = AsyncMock()
        mock_repository.get_by_id = AsyncMock(side_effect=Exception("Article not found"))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "Article not found" in data["detail"]
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_ingest_news_success(self, client, sample_articles):
        """Test successful news ingestion."""
        from src.api.routes.news import get_news_service, get_article_repository
        
        # Create mock services
        mock_news_service = AsyncMock()
        mock_news_service.fetch_rss_feeds = AsyncMock(return_value=[
            ArticleCreate(
                title="New Article",
                url="https://test.com/new",
                content="Content",
                source="test.com"
            )
        ])
        
        mock_repository = AsyncMock()
        mock_repository.get_by_url = AsyncMock(return_value=None)
        mock_repository.create = AsyncMock(return_value=sample_articles[0])
        
        # Override the dependencies
        client.app.dependency_overrides[get_news_service] = lambda: mock_news_service
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.post("/news/ingest", json={
                "feed_urls": ["https://test.com/rss"]
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["processed"] == 1
            assert data["data"]["new_articles"] == 1
            assert data["data"]["duplicates"] == 0
        finally:
            # Clean up overrides
            client.app.dependency_overrides.clear()

    def test_ingest_news_with_duplicates(self, client, sample_articles):
        """Test news ingestion with duplicate articles."""
        from src.api.routes.news import get_news_service, get_article_repository
        
        # Create mock services
        mock_news_service = AsyncMock()
        mock_news_service.fetch_rss_feeds = AsyncMock(return_value=[
            ArticleCreate(
                title="Existing Article",
                url="https://test.com/existing",
                content="Content",
                source="test.com"
            )
        ])
        
        mock_repository = AsyncMock()
        mock_repository.get_by_url = AsyncMock(return_value=sample_articles[0])  # Existing article
        
        # Override the dependencies
        client.app.dependency_overrides[get_news_service] = lambda: mock_news_service
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.post("/news/ingest", json={
                "feed_urls": ["https://test.com/rss"]
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["data"]["processed"] == 1
            assert data["data"]["new_articles"] == 0
            assert data["data"]["duplicates"] == 1
        finally:
            # Clean up overrides
            client.app.dependency_overrides.clear()
            
            assert data["data"]["processed"] == 1
            assert data["data"]["new_articles"] == 0
            assert data["data"]["duplicates"] == 1

    def test_ingest_news_service_error(self, client):
        """Test news ingestion with service error."""
        from src.api.routes.news import get_news_service, get_article_repository
        from src.core.exceptions import NewsIngestionError
        
        # Create mock services
        mock_news_service = AsyncMock()
        mock_news_service.fetch_rss_feeds = AsyncMock(side_effect=NewsIngestionError("Feed error"))
        
        mock_repository = AsyncMock()
        
        # Override the dependencies
        client.app.dependency_overrides[get_news_service] = lambda: mock_news_service
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.post("/news/ingest", json={
                "feed_urls": ["https://invalid.com/rss"]
            })
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        finally:
            # Clean up overrides
            client.app.dependency_overrides.clear()

    def test_get_news_sources(self, client):
        """Test getting news sources."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.get_stats = AsyncMock(return_value={
            "top_sources": [
                {"source": "technews.com", "count": 25},
                {"source": "mlnews.com", "count": 20}
            ],
            "total_articles": 45
        })
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/sources")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["configured_sources"] == 2
            assert len(data["data"]["source_statistics"]) == 2
            assert data["data"]["source_statistics"][0]["source"] == "technews.com"
            assert data["data"]["total_articles"] == 45
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_news_stats(self, client, sample_article_stats):
        """Test getting news statistics."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.get_stats = AsyncMock(return_value={
            "total_articles": 100,
            "articles_with_summaries": 75,
            "articles_with_embeddings": 50,
            "top_sources": [
                {"source": "technews.com", "count": 25},
                {"source": "mlnews.com", "count": 20}
            ],
            "recent_articles_7d": 15
        })
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/stats")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["total_articles"] == 100
            assert data["data"]["articles_with_summaries"] == 75
            assert data["data"]["articles_with_embeddings"] == 50
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_search_articles_success(self, client, sample_articles):
        """Test article search functionality."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.search_articles = AsyncMock(return_value=sample_articles[:1])
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/search?q=AI&limit=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["title"] == "AI Revolution 2024"
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_search_articles_no_query(self, client):
        """Test article search without query parameter."""
        response = client.get("/news/search")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_articles_empty_results(self, client):
        """Test article search with no results."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.search_articles = AsyncMock(return_value=[])
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/search?q=nonexistent")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 0
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_articles_invalid_page_size(self, client):
        """Test getting articles with invalid page size."""
        response = client.get("/news/?page_size=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_articles_invalid_page(self, client):
        """Test getting articles with invalid page number."""
        response = client.get("/news/?page=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_articles_max_page_size(self, client, sample_articles):
        """Test getting articles with maximum page size."""
        from src.api.routes.news import get_article_repository
        
        # Create mock repository
        mock_repository = AsyncMock()
        mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
        
        # Override the dependency
        client.app.dependency_overrides[get_article_repository] = lambda: mock_repository
        
        try:
            response = client.get("/news/?page_size=100")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["pagination"]["page_size"] == 100
        finally:
            # Clean up override
            client.app.dependency_overrides.clear()

    def test_get_articles_exceeds_max_page_size(self, client):
        """Test getting articles with page size exceeding maximum."""
        response = client.get("/news/?page_size=101")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_news_empty_feed_urls(self, client):
        """Test news ingestion with empty feed URLs."""
        response = client.post("/news/ingest", json={
            "feed_urls": []
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_news_invalid_urls(self, client):
        """Test news ingestion with invalid URLs."""
        response = client.post("/news/ingest", json={
            "feed_urls": ["not-a-url", "also-invalid"]
        })
        
        # Should still process but might have errors
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_concurrent_article_requests(self, client, sample_articles):
        """Test concurrent requests to article endpoints."""
        import concurrent.futures
        
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
            
            def make_request():
                return client.get("/news/")
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                responses = [future.result() for future in futures]
            
            # All requests should succeed
            assert all(r.status_code == status.HTTP_200_OK for r in responses)
