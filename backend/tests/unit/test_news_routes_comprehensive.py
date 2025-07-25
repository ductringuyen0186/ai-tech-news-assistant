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
    app.include_router(router, prefix="/api/news")
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
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
            
            response = client.get("/api/news/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]["items"]) == 2
            assert data["data"]["total"] == 2
            assert data["data"]["page"] == 1
            assert data["data"]["page_size"] == 20

    def test_get_articles_with_pagination(self, client, sample_articles):
        """Test getting articles with pagination parameters."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 10))
            
            response = client.get("/api/news/?page=2&page_size=5")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 5
            
            # Verify repository was called with correct offset
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            assert call_args[1]["limit"] == 5
            assert call_args[1]["offset"] == 5  # page 2, size 5 = offset 5

    def test_get_articles_with_filters(self, client, sample_articles):
        """Test getting articles with filter parameters."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 1))
            
            response = client.get("/api/news/?source=technews.com&author=John%20Doe&has_summary=true")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called with filters
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            assert call_args[1]["source"] == "technews.com"
            assert call_args[1]["author"] == "John Doe"
            assert call_args[1]["has_summary"] is True

    def test_get_articles_with_sorting(self, client, sample_articles):
        """Test getting articles with sorting parameters."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
            
            response = client.get("/api/news/?sort_by=view_count&sort_desc=false")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify repository was called with sorting
            mock_repository.list_articles.assert_called_once()
            call_args = mock_repository.list_articles.call_args
            assert call_args[1]["sort_by"] == "view_count"
            assert call_args[1]["sort_desc"] is False

    def test_get_article_by_id_success(self, client, sample_articles):
        """Test getting a specific article by ID."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.get_by_id = AsyncMock(return_value=sample_articles[0])
            
            response = client.get("/api/news/1")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["id"] == 1
            assert data["data"]["title"] == "AI Revolution 2024"

    def test_get_article_by_id_not_found(self, client):
        """Test getting non-existent article."""
        from src.core.exceptions import NotFoundError
        
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.get_by_id = AsyncMock(side_effect=NotFoundError("Article not found"))
            
            response = client.get("/api/news/999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False

    def test_ingest_news_success(self, client, sample_articles):
        """Test successful news ingestion."""
        with patch('src.api.routes.news.get_news_service') as mock_service, \
             patch('src.api.routes.news.get_article_repository') as mock_repo:
            
            mock_news_service = mock_service.return_value
            mock_news_service.fetch_rss_feeds = AsyncMock(return_value=[
                ArticleCreate(
                    title="New Article",
                    url="https://test.com/new",
                    content="Content",
                    source="test.com"
                )
            ])
            
            mock_repository = mock_repo.return_value
            mock_repository.get_by_url = AsyncMock(return_value=None)
            mock_repository.create = AsyncMock(return_value=sample_articles[0])
            
            response = client.post("/api/news/ingest", json={
                "feed_urls": ["https://test.com/rss"]
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["processed"] == 1
            assert data["data"]["new_articles"] == 1
            assert data["data"]["duplicates"] == 0

    def test_ingest_news_with_duplicates(self, client, sample_articles):
        """Test news ingestion with duplicate articles."""
        with patch('src.api.routes.news.get_news_service') as mock_service, \
             patch('src.api.routes.news.get_article_repository') as mock_repo:
            
            mock_news_service = mock_service.return_value
            mock_news_service.fetch_rss_feeds = AsyncMock(return_value=[
                ArticleCreate(
                    title="Existing Article",
                    url="https://test.com/existing",
                    content="Content",
                    source="test.com"
                )
            ])
            
            mock_repository = mock_repo.return_value
            mock_repository.get_by_url = AsyncMock(return_value=sample_articles[0])  # Existing article
            
            response = client.post("/api/news/ingest", json={
                "feed_urls": ["https://test.com/rss"]
            })
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["data"]["processed"] == 1
            assert data["data"]["new_articles"] == 0
            assert data["data"]["duplicates"] == 1

    def test_ingest_news_service_error(self, client):
        """Test news ingestion with service error."""
        from src.core.exceptions import NewsIngestionError
        
        with patch('src.api.routes.news.get_news_service') as mock_service:
            mock_news_service = mock_service.return_value
            mock_news_service.fetch_rss_feeds = AsyncMock(side_effect=NewsIngestionError("Feed error"))
            
            response = client.post("/api/news/ingest", json={
                "feed_urls": ["https://invalid.com/rss"]
            })
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_news_sources(self, client):
        """Test getting news sources."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.get_stats = AsyncMock(return_value={
                "top_sources": [
                    {"source": "technews.com", "count": 25},
                    {"source": "mlnews.com", "count": 20}
                ]
            })
            
            response = client.get("/api/news/sources")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]["sources"]) == 2
            assert data["data"]["sources"][0]["source"] == "technews.com"

    def test_get_news_stats(self, client, sample_article_stats):
        """Test getting news statistics."""
        with patch('src.api.routes.news.get_news_service') as mock_service:
            mock_news_service = mock_service.return_value
            mock_news_service.get_news_stats = AsyncMock(return_value=sample_article_stats)
            
            response = client.get("/api/news/stats")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["total_articles"] == 100
            assert data["data"]["articles_with_summaries"] == 75
            assert len(data["data"]["top_sources"]) == 2

    def test_search_articles_success(self, client, sample_articles):
        """Test article search functionality."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.search_articles = AsyncMock(return_value=sample_articles[:1])
            
            response = client.get("/api/news/search?q=AI&limit=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["title"] == "AI Revolution 2024"

    def test_search_articles_no_query(self, client):
        """Test article search without query parameter."""
        response = client.get("/api/news/search")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_articles_empty_results(self, client):
        """Test article search with no results."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.search_articles = AsyncMock(return_value=[])
            
            response = client.get("/api/news/search?q=nonexistent")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 0

    def test_get_articles_invalid_page_size(self, client):
        """Test getting articles with invalid page size."""
        response = client.get("/api/news/?page_size=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_articles_invalid_page(self, client):
        """Test getting articles with invalid page number."""
        response = client.get("/api/news/?page=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_articles_max_page_size(self, client, sample_articles):
        """Test getting articles with maximum page size."""
        with patch('src.api.routes.news.get_article_repository') as mock_repo:
            mock_repository = mock_repo.return_value
            mock_repository.list_articles = AsyncMock(return_value=(sample_articles, 2))
            
            response = client.get("/api/news/?page_size=100")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["data"]["page_size"] == 100

    def test_get_articles_exceeds_max_page_size(self, client):
        """Test getting articles with page size exceeding maximum."""
        response = client.get("/api/news/?page_size=101")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_news_empty_feed_urls(self, client):
        """Test news ingestion with empty feed URLs."""
        response = client.post("/api/news/ingest", json={
            "feed_urls": []
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_news_invalid_urls(self, client):
        """Test news ingestion with invalid URLs."""
        response = client.post("/api/news/ingest", json={
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
                return client.get("/api/news/")
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                responses = [future.result() for future in futures]
            
            # All requests should succeed
            assert all(r.status_code == status.HTTP_200_OK for r in responses)
