"""
Unit Tests for Health API Routes
================================

Tests for health check API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from pydantic import ValidationError

from src.api.routes.health import router, HealthResponse, ComponentHealth


class TestHealthRoutes:
    """Test cases for health check routes."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with health routes."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    def test_health_check_response_structure(self, client):
        """Test that health check response has correct structure."""
        response = client.get("/health")
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "timestamp", "version", "components"]
        for field in required_fields:
            assert field in data
        
        # Check components structure
        assert isinstance(data["components"], dict)
        
        # Each component should have status and optional details
        for component_name, component_data in data["components"].items():
            assert "status" in component_data
            assert component_data["status"] in ["healthy", "degraded", "unhealthy"]
    
    @patch('src.api.routes.health.get_article_repository')
    @patch('src.api.routes.health.get_embedding_service')
    @patch('src.api.routes.health.get_news_service')
    @patch('src.api.routes.health.get_summarization_service')
    def test_detailed_health_check_all_healthy(
        self, 
        mock_summarization_service,
        mock_news_service,
        mock_embedding_service,
        mock_article_repo,
        client
    ):
        """Test detailed health check when all components are healthy."""
        # Mock all services as healthy
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_accessible": True,
            "total_articles": 100
        })
        
        mock_embedding_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "model_loaded": True,
            "gpu_available": False
        })
        
        mock_news_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "feeds_accessible": 2,
            "feeds_total": 2
        })
        
        mock_summarization_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "api_accessible": True,
            "model": "gpt-3.5-turbo"
        })
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["components"]["database"]["status"] == "healthy"
        assert data["components"]["embedding_service"]["status"] == "healthy"
        assert data["components"]["news_service"]["status"] == "healthy"
        assert data["components"]["summarization_service"]["status"] == "healthy"
    
    @patch('src.api.routes.health.get_article_repository')
    @patch('src.api.routes.health.get_embedding_service')
    @patch('src.api.routes.health.get_news_service')
    @patch('src.api.routes.health.get_summarization_service')
    def test_detailed_health_check_some_degraded(
        self, 
        mock_summarization_service,
        mock_news_service,
        mock_embedding_service,
        mock_article_repo,
        client
    ):
        """Test detailed health check when some components are degraded."""
        # Mock database as healthy
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_accessible": True,
            "total_articles": 100
        })
        
        # Mock embedding service as degraded
        mock_embedding_service.return_value.health_check = AsyncMock(return_value={
            "status": "degraded",
            "model_loaded": True,
            "gpu_available": False,
            "warning": "GPU not available, using CPU"
        })
        
        # Mock news service as healthy
        mock_news_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "feeds_accessible": 2,
            "feeds_total": 2
        })
        
        # Mock summarization service as degraded
        mock_summarization_service.return_value.health_check = AsyncMock(return_value={
            "status": "degraded",
            "api_accessible": True,
            "model": "gpt-3.5-turbo",
            "warning": "High API latency"
        })
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "degraded"  # Overall status should be degraded
        assert data["components"]["database"]["status"] == "healthy"
        assert data["components"]["embedding_service"]["status"] == "degraded"
        assert data["components"]["news_service"]["status"] == "healthy"
        assert data["components"]["summarization_service"]["status"] == "degraded"
    
    @patch('src.api.routes.health.get_article_repository')
    @patch('src.api.routes.health.get_embedding_service')
    @patch('src.api.routes.health.get_news_service')
    @patch('src.api.routes.health.get_summarization_service')
    def test_detailed_health_check_some_unhealthy(
        self, 
        mock_summarization_service,
        mock_news_service,
        mock_embedding_service,
        mock_article_repo,
        client
    ):
        """Test detailed health check when some components are unhealthy."""
        # Mock database as unhealthy
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "unhealthy",
            "database_accessible": False,
            "error": "Database connection failed"
        })
        
        # Mock other services as healthy
        mock_embedding_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "model_loaded": True
        })
        
        mock_news_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "feeds_accessible": 2,
            "feeds_total": 2
        })
        
        mock_summarization_service.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "api_accessible": True
        })
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"  # Overall status should be unhealthy
        assert data["components"]["database"]["status"] == "unhealthy"
    
    @patch('src.api.routes.health.get_article_repository')
    def test_detailed_health_check_service_exception(self, mock_article_repo, client):
        """Test detailed health check when service raises exception."""
        # Mock service to raise exception
        mock_article_repo.return_value.health_check = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle exceptions gracefully
        assert data["status"] in ["degraded", "unhealthy"]
        assert data["components"]["database"]["status"] == "unhealthy"
        assert "message" in data["components"]["database"]
        assert "Service unavailable" in data["components"]["database"]["message"]
    
    @patch('src.api.routes.health.get_article_repository')
    def test_readiness_check(self, mock_article_repo, client):
        """Test readiness check endpoint."""
        # Mock repository to return healthy status
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_accessible": True
        })
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ready" in data
        assert isinstance(data["ready"], bool)
        assert "timestamp" in data
    
    @patch('src.api.routes.health.get_article_repository')
    def test_readiness_check_database_accessible(self, mock_article_repo, client):
        """Test readiness check when database is accessible."""
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "healthy",
            "database_accessible": True
        })
        
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ready"] is True
    
    @patch('src.api.routes.health.get_article_repository')
    def test_readiness_check_database_inaccessible(self, mock_article_repo, client):
        """Test readiness check when database is not accessible."""
        mock_article_repo.return_value.health_check = AsyncMock(return_value={
            "status": "unhealthy",
            "database_accessible": False
        })
        
        response = client.get("/health/ready")
        
        assert response.status_code == 503  # Service Unavailable
        data = response.json()
        
        assert data["ready"] is False
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alive" in data
        assert data["alive"] is True
        assert "timestamp" in data
        assert "uptime" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for basic metrics
        assert "timestamp" in data
        assert "uptime" in data
        assert "system" in data
        
        # Check system metrics structure
        system_metrics = data["system"]
        assert "cpu_usage" in system_metrics
        assert "memory_usage" in system_metrics
        assert "disk_usage" in system_metrics
    
    @patch('src.api.routes.health.get_article_repository')
    @patch('src.api.routes.health.get_embedding_service')
    @patch('src.api.routes.health.get_news_service')
    @patch('src.api.routes.health.get_summarization_service')
    def test_metrics_with_service_stats(
        self, 
        mock_summarization_service,
        mock_news_service,
        mock_embedding_service,
        mock_article_repo,
        client
    ):
        """Test metrics endpoint with service-specific statistics."""
        # Mock services to return stats
        mock_article_repo.return_value.get_stats = AsyncMock(return_value={
            "total_articles": 500,
            "articles_with_summaries": 300,
            "articles_with_embeddings": 250
        })
        
        mock_embedding_service.return_value.get_stats = AsyncMock(return_value={
            "total_embeddings": 250,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
        })
        
        mock_news_service.return_value.get_stats = AsyncMock(return_value={
            "configured_feeds": 5,
            "last_fetch_time": "2024-01-01T12:00:00Z"
        })
        
        mock_summarization_service.return_value.get_stats = AsyncMock(return_value={
            "total_summaries": 300,
            "average_processing_time": 2.5
        })
        
        response = client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "services" in data
        services = data["services"]
        
        assert "database" in services
        assert services["database"]["total_articles"] == 500
        
        assert "embedding_service" in services
        assert services["embedding_service"]["total_embeddings"] == 250
        
        assert "news_service" in services
        assert services["news_service"]["configured_feeds"] == 5
        
        assert "summarization_service" in services
        assert services["summarization_service"]["total_summaries"] == 300


class TestHealthResponseModels:
    """Test health response models and validation."""
    
    def test_health_response_model(self):
        """Test HealthResponse model validation."""
        # Valid response
        response = HealthResponse(
            status="healthy",
            timestamp="2024-01-01T12:00:00Z",
            version="1.0.0",
            components={
                "database": ComponentHealth(name="database", status="healthy"),
                "api": ComponentHealth(name="api", status="degraded", details={"warning": "High latency"})
            }
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert len(response.components) == 2
    
    def test_component_health_model(self):
        """Test ComponentHealth model validation."""
        # Healthy component
        component = ComponentHealth(name="database", status="healthy")
        assert component.name == "database"
        assert component.status == "healthy"
        assert component.details is None
        
        # Component with details
        component_with_details = ComponentHealth(
            status="degraded",
            details={"warning": "Performance degraded", "cpu_usage": 85}
        )
        assert component_with_details.status == "degraded"
        assert component_with_details.details["warning"] == "Performance degraded"
    
    def test_invalid_status_values(self):
        """Test that invalid status values are rejected."""
        with pytest.raises(ValidationError):
            ComponentHealth(status="invalid_status")
        
        with pytest.raises(ValidationError):
            HealthResponse(
                status="invalid_status",
                timestamp="2024-01-01T12:00:00Z",
                version="1.0.0",
                components={}
            )


class TestHealthUtilities:
    """Test health check utility functions."""
    
    @patch('src.api.routes.health.psutil')
    def test_get_system_metrics(self, mock_psutil):
        """Test system metrics collection."""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value.percent = 67.8
        mock_psutil.disk_usage.return_value.percent = 23.4
        
        from src.api.routes.health import get_system_metrics
        
        metrics = get_system_metrics()
        
        assert metrics["cpu_usage"] == 45.5
        assert metrics["memory_usage"] == 67.8
        assert metrics["disk_usage"] == 23.4
    
    def test_determine_overall_status(self):
        """Test overall status determination logic."""
        from src.api.routes.health import determine_overall_status
        
        # All healthy
        components = {
            "db": {"status": "healthy"},
            "api": {"status": "healthy"}
        }
        assert determine_overall_status(components) == "healthy"
        
        # Some degraded
        components = {
            "db": {"status": "healthy"},
            "api": {"status": "degraded"}
        }
        assert determine_overall_status(components) == "degraded"
        
        # Some unhealthy
        components = {
            "db": {"status": "unhealthy"},
            "api": {"status": "healthy"}
        }
        assert determine_overall_status(components) == "unhealthy"
        
        # Mixed degraded and unhealthy
        components = {
            "db": {"status": "unhealthy"},
            "api": {"status": "degraded"},
            "cache": {"status": "healthy"}
        }
        assert determine_overall_status(components) == "unhealthy"
    
    def test_format_uptime(self):
        """Test uptime formatting."""
        from src.api.routes.health import format_uptime
        
        # Test various uptime values
        assert format_uptime(30) == "30 seconds"
        assert format_uptime(90) == "1 minute 30 seconds"
        assert format_uptime(3661) == "1 hour 1 minute 1 second"
        assert format_uptime(90061) == "1 day 1 hour 1 minute 1 second"
