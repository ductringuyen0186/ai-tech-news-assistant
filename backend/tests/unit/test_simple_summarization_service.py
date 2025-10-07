"""
Simple Summarization Service Tests
==================================

Basic working tests for SummarizationService to improve coverage.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.summarization_service import SummarizationService
from src.models.article import SummarizationRequest, ArticleSummary
from src.core.exceptions import ValidationError


class TestSimpleSummarizationService:
    """Simple test cases for SummarizationService."""
    
    @pytest.fixture
    def service(self):
        """Create a summarization service instance."""
        return SummarizationService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.client is not None
        assert service.anthropic_client is not None
        assert service.request_timeout == 120.0
        assert service.max_retries == 3
    
    @pytest.mark.asyncio
    async def test_summarize_content_basic(self, service):
        """Test basic content summarization with mocked response."""
        request = SummarizationRequest(
            content="This is a long article about artificial intelligence and machine learning.",
            max_length=50,
            style="concise"
        )
        
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI summary text"
        mock_response.usage.total_tokens = 50
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            result = await service.summarize_content(request)
            
        assert isinstance(result, ArticleSummary)
        assert "AI summary text" in result.summary
        
    @pytest.mark.asyncio 
    async def test_summarize_content_validation_error(self, service):
        """Test summarization with validation error."""
        request = SummarizationRequest(
            content="",  # Empty content should cause validation error
            max_length=50
        )
        
        with pytest.raises(ValidationError):
            await service.summarize_content(request)
    
    def test_prepare_content(self, service):
        """Test content preparation method."""
        content = "  This is content with   extra spaces   "
        prepared = service._prepare_content(content)
        assert "This is content with extra spaces" in prepared
        
    def test_create_summary_prompt(self, service):
        """Test summary prompt creation."""
        content = "Test content"
        style = "concise"
        max_length = 100
        
        prompt = service._create_summary_prompt(content, style, max_length)
        assert "Test content" in prompt
        assert "concise" in prompt.lower()
        assert "100" in prompt
        
    @pytest.mark.asyncio
    async def test_batch_summarize_basic(self, service):
        """Test batch summarization."""
        requests = [
            SummarizationRequest(content="Content 1", max_length=50),
            SummarizationRequest(content="Content 2", max_length=50)
        ]
        
        # Mock responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary"
        mock_response.usage.total_tokens = 25
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            results = await service.batch_summarize(requests)
            
        assert len(results) == 2
        assert all(isinstance(r, ArticleSummary) for r in results)
        
    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test service health check."""
        # Mock successful API call
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            health = await service.health_check()
            
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
