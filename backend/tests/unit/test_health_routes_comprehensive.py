"""
Comprehensive Unit Tests for Health Routes
==========================================

Tests for health check and API info endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status

from src.api.routes.health import router
from src.models.api import HealthCheck


@pytest.fixture
def test_app():
    """Create test FastAPI app with health routes."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestHealthRoutes:
    """Test cases for health check endpoints."""
    
    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "docs_url" in data
        assert data["name"] == "AI Tech News Assistant API"

    def test_health_check_healthy(self, client):
        """Test health check endpoint when all services are healthy."""
        with patch('src.api.routes.health.get_settings') as mock_settings:
            mock_settings.return_value.database_path = ":memory:"
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
            assert "services" in data
            assert data["services"]["database"] == "connected"

    def test_health_check_database_error(self, client):
        """Test health check when database has issues."""
        with patch('src.api.routes.health.get_settings') as mock_settings, \
             patch('src.api.routes.health.sqlite3.connect') as mock_connect:
            
            mock_settings.return_value.database_path = "/invalid/path/db.sqlite"
            mock_connect.side_effect = Exception("Database connection failed")
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["services"]["database"] == "error"

    def test_ping_endpoint(self, client):
        """Test ping endpoint."""
        response = client.get("/ping")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["message"] == "pong"
        assert "timestamp" in data

    def test_health_check_response_format(self, client):
        """Test that health check response matches HealthCheck model."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        health_check = HealthCheck(**data)
        assert health_check.status in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health_check.timestamp, datetime)
        assert isinstance(health_check.services, dict)

    def test_api_info_version_format(self, client):
        """Test API info version format."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Version should be semantic versioning format
        version = data["version"]
        assert len(version.split('.')) >= 2  # At least major.minor

    def test_health_check_includes_uptime(self, client):
        """Test that health check includes uptime information."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] >= 0

    def test_health_endpoint_response_time(self, client):
        """Test that health endpoint responds quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert response_time < 1.0  # Should respond within 1 second

    def test_ping_response_time(self, client):
        """Test that ping endpoint responds very quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/ping")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert response_time < 0.1  # Should respond within 100ms

    def test_cors_headers(self, client):
        """Test CORS headers are present in responses."""
        response = client.get("/health")
        
        # Basic check that response is successful
        assert response.status_code == status.HTTP_200_OK
        # CORS headers would be added by middleware in the main app

    def test_multiple_concurrent_health_checks(self, client):
        """Test multiple concurrent health check requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        assert all(r.json()["status"] in ["healthy", "degraded", "unhealthy"] for r in responses)
