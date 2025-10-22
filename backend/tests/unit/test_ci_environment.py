"""
Unit Tests for AI Tech News Assistant
======================================
Tests that run in CI/CD without external dependencies like Ollama.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))


class TestAppImports:
    """Test that core imports work without external dependencies."""
    
    def test_main_import(self):
        """Test that main can be imported."""
        import main
        assert hasattr(main, 'app')
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app is created successfully."""
        from main import app
        assert app is not None
        assert hasattr(app, 'routes')


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_import(self):
        """Test settings can be imported and instantiated."""
        from utils.config import get_settings, Settings
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.app_name is not None
    
    def test_settings_with_env_vars(self):
        """Test settings load from environment variables."""
        os.environ['APP_NAME'] = 'Test App'
        os.environ['DEBUG'] = 'true'
        
        from utils.config import Settings
        settings = Settings()
        
        assert settings.app_name == 'Test App'
        assert settings.debug is True


class TestLLMProvidersMocked:
    """Test LLM providers with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_ollama_provider_availability_check(self):
        """Test OllamaProvider availability check with mock."""
        from llm.providers import OllamaProvider
        
        provider = OllamaProvider(
            base_url="http://mock:11434",
            model="test-model"
        )
        
        # Mock the HTTP client
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "test-model"}]
            }
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            is_available = await provider.is_available()
            assert is_available is True
    
    @pytest.mark.asyncio
    async def test_ollama_provider_unavailable(self):
        """Test OllamaProvider handles unavailable server gracefully."""
        from llm.providers import OllamaProvider
        
        provider = OllamaProvider(
            base_url="http://mock:11434",
            model="test-model"
        )
        
        # Mock connection failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            
            is_available = await provider.is_available()
            assert is_available is False
    
    @pytest.mark.asyncio
    async def test_ollama_provider_summarize_success(self):
        """Test OllamaProvider summarization with mock."""
        from llm.providers import OllamaProvider
        
        provider = OllamaProvider(
            base_url="http://mock:11434",
            model="test-model"
        )
        
        # Mock successful summarization
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "This is a test summary of an AI article."
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await provider.summarize("Test article content")
            
            assert result['success'] is True
            assert 'summary' in result
            assert 'keywords' in result
            assert result['provider'] == 'ollama'
    
    @pytest.mark.asyncio
    async def test_ollama_provider_empty_text(self):
        """Test OllamaProvider handles empty text gracefully."""
        from llm.providers import OllamaProvider
        
        provider = OllamaProvider(
            base_url="http://mock:11434",
            model="test-model"
        )
        
        result = await provider.summarize("")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Empty text' in result['error']


class TestAPIEndpoints:
    """Test API endpoints with mocked dependencies."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        # Check for API info fields
        assert "name" in data or "service" in data or "endpoints" in data
    
    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestUtilities:
    """Test utility functions."""
    
    def test_logger_creation(self):
        """Test logger can be created."""
        from utils.logger import get_logger
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"


def run_tests():
    """Run all tests."""
    import pytest
    
    # Run tests with verbose output
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-W', 'ignore::DeprecationWarning'
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
