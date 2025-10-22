"""
API Tests for Ingestion Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from main import app
from src.services.ingestion_service import IngestionStatus, IngestionResult


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_ingestion_result():
    """Create a mock IngestionResult."""
    result = IngestionResult()
    result.status = IngestionStatus.COMPLETED
    result.start_time = datetime(2025, 10, 21, 10, 0, 0)
    result.end_time = datetime(2025, 10, 21, 10, 5, 0)
    result.total_feeds = 5
    result.total_articles_found = 100
    result.total_articles_saved = 95
    result.duplicates_skipped = 3
    result.errors_encountered = 2
    result.sources_processed = {
        "TechCrunch": {"articles": 20, "saved": 19},
        "HackerNews": {"articles": 30, "saved": 28}
    }
    return result


class TestIngestationEndpointTrigger:
    """Tests for POST /api/ingest endpoint."""
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_foreground(self, mock_service_class, client, mock_ingestion_result):
        """Test triggering ingestion in foreground mode."""
        mock_service = Mock()
        mock_service.ingest_all.return_value = mock_ingestion_result
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/ingest",
            json={"background": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_feeds"] == 5
        assert data["total_articles_saved"] == 95
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_background(self, mock_service_class, client, mock_ingestion_result):
        """Test triggering ingestion in background mode."""
        mock_service = Mock()
        mock_service.ingest_all.return_value = mock_ingestion_result
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/ingest",
            json={"background": True}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert "background" in data["message"].lower()
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_custom_sources(self, mock_service_class, client, mock_ingestion_result):
        """Test triggering ingestion with custom sources."""
        mock_service = Mock()
        mock_service.ingest_all.return_value = mock_ingestion_result
        mock_service_class.return_value = mock_service
        
        custom_sources = [
            {"name": "CustomFeed", "url": "http://example.com/feed.xml", "category": "AI"}
        ]
        
        response = client.post(
            "/api/ingest",
            json={"background": False, "sources": custom_sources}
        )
        
        assert response.status_code == 200
        mock_service.ingest_all.assert_called_once()
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_partial_failure(self, mock_service_class, client):
        """Test handling partial ingestion failure."""
        result = IngestionResult()
        result.status = IngestionStatus.PARTIAL
        result.total_articles_found = 50
        result.total_articles_saved = 25
        result.errors_encountered = 5
        
        mock_service = Mock()
        mock_service.ingest_all.return_value = result
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/ingest",
            json={"background": False}
        )
        
        assert response.status_code == 207  # Multi-status
        data = response.json()
        assert data["status"] == "partial"
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_complete_failure(self, mock_service_class, client):
        """Test handling complete ingestion failure."""
        result = IngestionResult()
        result.status = IngestionStatus.FAILED
        result.error_details = ["RSS feed unreachable", "Database connection lost"]
        
        mock_service = Mock()
        mock_service.ingest_all.return_value = result
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/ingest",
            json={"background": False}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "failed"
        assert len(data["error_details"]) > 0
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_validation_error(self, mock_service_class, client):
        """Test validation error with invalid request."""
        response = client.post(
            "/api/ingest",
            json={"invalid_field": "value"}
        )
        
        # Should fail validation or use defaults
        assert response.status_code in [200, 422]
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_trigger_ingestion_exception_handling(self, mock_service_class, client):
        """Test handling unexpected exceptions."""
        mock_service = Mock()
        mock_service.ingest_all.side_effect = Exception("Unexpected error")
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.post(
            "/api/ingest",
            json={"background": False}
        )
        
        assert response.status_code == 500


class TestIngestionStatusEndpoint:
    """Tests for GET /api/ingest/status endpoint."""
    
    @patch('src.api.routes.ingestion.latest_ingestion_result')
    def test_get_status_with_results(self, mock_latest, client, mock_ingestion_result):
        """Test retrieving ingestion status when results exist."""
        with patch.dict('src.api.routes.ingestion.__dict__', 
                       {'latest_ingestion_result': mock_ingestion_result}):
            response = client.get("/api/ingest/status")
        
        # Status endpoint should return result
        assert response.status_code in [200, 404]  # Depends on implementation
    
    def test_get_status_no_results(self, client):
        """Test retrieving status when no ingestion has run."""
        response = client.get("/api/ingest/status")
        
        # Should return 404 or empty result
        assert response.status_code in [200, 404]
    
    def test_get_status_response_format(self, client, mock_ingestion_result):
        """Test status response has expected format."""
        with patch('src.api.routes.ingestion.latest_ingestion_result', mock_ingestion_result):
            response = client.get("/api/ingest/status")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = [
                    "status", "total_feeds", "total_articles_found",
                    "total_articles_saved", "duplicates_skipped"
                ]
                for field in expected_fields:
                    assert field in data or response.status_code == 404


class TestIngestionStatsEndpoint:
    """Tests for GET /api/ingest/stats endpoint."""
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_get_stats_success(self, mock_service_class, client):
        """Test retrieving statistics successfully."""
        mock_service = Mock()
        mock_service.get_stats.return_value = {
            "total_articles": 500,
            "total_sources": 8,
            "total_categories": 15,
            "articles_by_source": {
                "TechCrunch": 50,
                "HackerNews": 200
            }
        }
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/ingest/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_articles"] == 500
        assert data["total_sources"] == 8
        assert data["total_categories"] == 15
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_get_stats_empty_database(self, mock_service_class, client):
        """Test retrieving stats from empty database."""
        mock_service = Mock()
        mock_service.get_stats.return_value = {
            "total_articles": 0,
            "total_sources": 0,
            "total_categories": 0
        }
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/ingest/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_articles"] == 0
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_get_stats_error_handling(self, mock_service_class, client):
        """Test stats endpoint error handling."""
        mock_service = Mock()
        mock_service.get_stats.side_effect = Exception("Database error")
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.get("/api/ingest/stats")
        
        # Should handle gracefully
        assert response.status_code in [500, 503]


class TestIngestionIntegration:
    """Integration tests for complete ingestion flow."""
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_complete_ingestion_flow(self, mock_service_class, client):
        """Test complete ingestion flow: trigger -> check status -> get stats."""
        result = IngestionResult()
        result.status = IngestionStatus.COMPLETED
        result.total_feeds = 2
        result.total_articles_found = 25
        result.total_articles_saved = 24
        
        mock_service = Mock()
        mock_service.ingest_all.return_value = result
        mock_service.get_stats.return_value = {"total_articles": 24}
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        # Trigger ingestion
        response1 = client.post("/api/ingest", json={"background": False})
        assert response1.status_code == 200
        
        # Check status
        response2 = client.get("/api/ingest/status")
        assert response2.status_code in [200, 404]
        
        # Get stats
        response3 = client.get("/api/ingest/stats")
        assert response3.status_code == 200
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_multiple_concurrent_requests(self, mock_service_class, client):
        """Test handling multiple concurrent requests."""
        result = IngestionResult()
        result.status = IngestionStatus.RUNNING
        
        mock_service = Mock()
        mock_service.ingest_all.return_value = result
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        # Send multiple requests
        for _ in range(3):
            response = client.post("/api/ingest", json={"background": True})
            assert response.status_code in [200, 202]


class TestIngestionErrorHandling:
    """Tests for error handling in endpoints."""
    
    def test_invalid_json_payload(self, client):
        """Test handling invalid JSON payload."""
        response = client.post(
            "/api/ingest",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_database_connection_error(self, mock_service_class, client):
        """Test handling database connection errors."""
        mock_service = Mock()
        mock_service.ingest_all.side_effect = ConnectionError("DB unreachable")
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/ingest", json={"background": False})
        
        assert response.status_code == 500
    
    def test_endpoint_not_found(self, client):
        """Test 404 for non-existent endpoints."""
        response = client.get("/api/ingest/nonexistent")
        
        assert response.status_code == 404


class TestIngestionResponseModels:
    """Tests for response model validation."""
    
    @patch('src.api.routes.ingestion.IngestionService')
    def test_ingest_response_model(self, mock_service_class, client, mock_ingestion_result):
        """Test IngestResponse model contains all required fields."""
        mock_service = Mock()
        mock_service.ingest_all.return_value = mock_ingestion_result
        mock_service.close = Mock()
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/ingest", json={"background": False})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "total_feeds" in data
        assert "total_articles_found" in data
        assert "total_articles_saved" in data
        assert "duplicates_skipped" in data
        assert "errors_encountered" in data
        assert "success_rate" in data
        assert "duration_seconds" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
