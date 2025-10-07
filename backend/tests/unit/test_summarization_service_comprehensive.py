"""
Comprehensive Unit Tests for Summarization Service
==================================================

Tests for summarization service LLM operations.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock

import httpx

from src.services.summarization_service import SummarizationService
from src.models.article import SummarizationRequest, ArticleSummary
from src.core.exceptions import LLMError, ValidationError


class TestSummarizationService:
    """Test cases for SummarizationService."""
    
    @pytest.fixture
    def summarization_service(self):
        """Create summarization service instance."""
        return SummarizationService()
    
    @pytest.fixture
    def sample_summarization_request(self):
        """Sample summarization request."""
        return SummarizationRequest(
            content="This is a long article about artificial intelligence and machine learning technologies. " * 20,
            max_length=150,
            style="concise",
            include_key_points=True,
            language="en"
        )
    
    @pytest.fixture
    def sample_ollama_response(self):
        """Sample Ollama API response."""
        return {
            "model": "llama2",
            "response": "AI and ML technologies are rapidly advancing, enabling new capabilities in automation and decision-making across various industries.",
            "done": True,
            "context": [],
            "total_duration": 1234567890,
            "load_duration": 123456,
            "prompt_eval_duration": 234567,
            "eval_duration": 345678
        }
    
    @pytest.fixture
    def sample_claude_response(self):
        """Sample Claude API response."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Artificial intelligence and machine learning are transforming industries through advanced automation and intelligent decision-making capabilities."
                }
            ],
            "id": "msg_123",
            "model": "claude-3-sonnet-20240229",
            "role": "assistant",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 150,
                "output_tokens": 50
            }
        }

    @pytest.mark.asyncio
    async def test_initialize_service(self, summarization_service):
        """Test service initialization."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = "test-api-key"
            
            await summarization_service.initialize()
            
            assert summarization_service.ollama_client is not None
            assert summarization_service.claude_client is not None
            assert summarization_service.max_content_length == 50000
            assert summarization_service.request_timeout == 120.0

    @pytest.mark.asyncio
    async def test_initialize_ollama_only(self, summarization_service):
        """Test initialization with only Ollama configured."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = None
            
            await summarization_service.initialize()
            
            assert summarization_service.ollama_client is not None
            assert summarization_service.claude_client is None

    @pytest.mark.asyncio
    async def test_initialize_claude_only(self, summarization_service):
        """Test initialization with only Claude configured."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = None
            mock_settings.claude_api_key = "test-api-key"
            
            await summarization_service.initialize()
            
            assert summarization_service.ollama_client is None
            assert summarization_service.claude_client is not None

    @pytest.mark.asyncio
    async def test_cleanup_service(self, summarization_service):
        """Test service cleanup."""
        # Initialize first
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = "test-api-key"
            await summarization_service.initialize()
        
        # Mock the aclose methods
        summarization_service.ollama_client.aclose = AsyncMock()
        summarization_service.claude_client.aclose = AsyncMock()
        
        await summarization_service.cleanup()
        
        assert summarization_service.ollama_client is None
        assert summarization_service.claude_client is None

    def test_validate_request_valid(self, summarization_service, sample_summarization_request):
        """Test request validation with valid request."""
        # Should not raise any exception
        summarization_service._validate_request(sample_summarization_request)

    def test_validate_request_empty_content(self, summarization_service):
        """Test request validation with empty content."""
        request = SummarizationRequest(content="", max_length=150)
        
        with pytest.raises(ValidationError, match="Content cannot be empty"):
            summarization_service._validate_request(request)

    def test_validate_request_content_too_long(self, summarization_service):
        """Test request validation with content too long."""
        long_content = "A" * 60000  # Exceeds max_content_length
        request = SummarizationRequest(content=long_content, max_length=150)
        
        with pytest.raises(ValidationError, match="Content too long"):
            summarization_service._validate_request(request)

    def test_validate_request_invalid_max_length(self, summarization_service):
        """Test request validation with invalid max length."""
        request = SummarizationRequest(content="Test content", max_length=0)
        
        with pytest.raises(ValidationError, match="Invalid max_length"):
            summarization_service._validate_request(request)

    def test_prepare_content(self, summarization_service):
        """Test content preparation."""
        # Test HTML removal
        html_content = "This is <b>bold</b> and <i>italic</i> text with <script>alert('test')</script>"
        prepared = summarization_service._prepare_content(html_content)
        assert "<b>" not in prepared
        assert "<script>" not in prepared
        assert "bold" in prepared
        assert "italic" in prepared
        
        # Test whitespace normalization
        spaced_content = "Too   much    whitespace\n\n\nhere"
        prepared = summarization_service._prepare_content(spaced_content)
        assert "Too much whitespace here" in prepared

    @pytest.mark.asyncio
    async def test_summarize_with_ollama_success(self, summarization_service, sample_summarization_request, sample_ollama_response):
        """Test successful summarization with Ollama."""
        mock_response = Mock()
        mock_response.json.return_value = sample_ollama_response
        mock_response.raise_for_status = Mock()
        
        summarization_service.ollama_client = Mock()
        summarization_service.ollama_client.post = AsyncMock(return_value=mock_response)
        
        summary = await summarization_service._summarize_with_ollama(
            sample_summarization_request.content,
            sample_summarization_request.max_length,
            sample_summarization_request.style
        )
        
        assert summary == sample_ollama_response["response"]
        summarization_service.ollama_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_with_ollama_http_error(self, summarization_service, sample_summarization_request):
        """Test Ollama summarization with HTTP error."""
        summarization_service.ollama_client = Mock()
        summarization_service.ollama_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "500 Internal Server Error", request=Mock(), response=Mock()
        ))
        
        with pytest.raises(LLMError, match="Ollama request failed"):
            await summarization_service._summarize_with_ollama(
                sample_summarization_request.content,
                sample_summarization_request.max_length,
                sample_summarization_request.style
            )

    @pytest.mark.asyncio
    async def test_summarize_with_claude_success(self, summarization_service, sample_summarization_request, sample_claude_response):
        """Test successful summarization with Claude."""
        mock_response = Mock()
        mock_response.json.return_value = sample_claude_response
        mock_response.raise_for_status = Mock()
        
        summarization_service.claude_client = Mock()
        summarization_service.claude_client.post = AsyncMock(return_value=mock_response)
        
        summary = await summarization_service._summarize_with_claude(
            sample_summarization_request.content,
            sample_summarization_request.max_length,
            sample_summarization_request.style
        )
        
        expected_summary = sample_claude_response["content"][0]["text"]
        assert summary == expected_summary

    @pytest.mark.asyncio
    async def test_summarize_with_claude_api_error(self, summarization_service, sample_summarization_request):
        """Test Claude summarization with API error."""
        error_response = Mock()
        error_response.status_code = 429
        error_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        
        summarization_service.claude_client = Mock()
        summarization_service.claude_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "429 Too Many Requests", request=Mock(), response=error_response
        ))
        
        with pytest.raises(LLMError, match="Claude API request failed"):
            await summarization_service._summarize_with_claude(
                sample_summarization_request.content,
                sample_summarization_request.max_length,
                sample_summarization_request.style
            )

    def test_build_summarization_prompt_concise(self, summarization_service):
        """Test building concise summarization prompt."""
        content = "Long article content about AI technology"
        max_length = 100
        style = "concise"
        
        prompt = summarization_service._build_summarization_prompt(content, max_length, style)
        
        assert "concise" in prompt.lower()
        assert "100" in prompt
        assert "AI technology" in prompt

    def test_build_summarization_prompt_detailed(self, summarization_service):
        """Test building detailed summarization prompt."""
        content = "Article about machine learning"
        max_length = 200
        style = "detailed"
        
        prompt = summarization_service._build_summarization_prompt(content, max_length, style)
        
        assert "detailed" in prompt.lower()
        assert "200" in prompt
        assert "machine learning" in prompt

    def test_build_summarization_prompt_bullet_points(self, summarization_service):
        """Test building bullet points summarization prompt."""
        content = "News article content"
        max_length = 150
        style = "bullet_points"
        
        prompt = summarization_service._build_summarization_prompt(content, max_length, style)
        
        assert "bullet points" in prompt.lower() or "bullet" in prompt.lower()
        assert "150" in prompt

    def test_post_process_summary(self, summarization_service):
        """Test summary post-processing."""
        # Test basic cleaning
        raw_summary = "  This is a summary with extra spaces.  \n\n"
        processed = summarization_service._post_process_summary(raw_summary)
        assert processed == "This is a summary with extra spaces."
        
        # Test quote removal
        quoted_summary = '"This is a quoted summary."'
        processed = summarization_service._post_process_summary(quoted_summary)
        assert processed == "This is a quoted summary."
        
        # Test length truncation
        long_summary = "A" * 1000
        processed = summarization_service._post_process_summary(long_summary)
        assert len(processed) <= 800

    @pytest.mark.asyncio
    async def test_summarize_content_ollama_success(self, summarization_service, sample_summarization_request, sample_ollama_response):
        """Test full summarization with Ollama success."""
        # Mock initialization
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = None
            
            # Mock Ollama response
            mock_response = Mock()
            mock_response.json.return_value = sample_ollama_response
            mock_response.raise_for_status = Mock()
            
            summarization_service.ollama_client = Mock()
            summarization_service.ollama_client.post = AsyncMock(return_value=mock_response)
            
            result = await summarization_service.summarize_content(sample_summarization_request)
            
            assert isinstance(result, ArticleSummary)
            assert result.summary == sample_ollama_response["response"]
            assert result.word_count > 0
            assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_summarize_content_fallback_to_claude(self, summarization_service, sample_summarization_request, sample_claude_response):
        """Test summarization fallback from Ollama to Claude."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = "test-api-key"
            
            # Mock Ollama failure
            ollama_client = Mock()
            ollama_client.post = AsyncMock(side_effect=LLMError("Ollama failed"))
            
            # Mock Claude success
            claude_mock_response = Mock()
            claude_mock_response.json.return_value = sample_claude_response
            claude_mock_response.raise_for_status = Mock()
            
            claude_client = Mock()
            claude_client.post = AsyncMock(return_value=claude_mock_response)
            
            summarization_service.ollama_client = ollama_client
            summarization_service.claude_client = claude_client
            
            result = await summarization_service.summarize_content(sample_summarization_request)
            
            assert isinstance(result, ArticleSummary)
            assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_summarize_content_all_providers_fail(self, summarization_service, sample_summarization_request):
        """Test summarization when all providers fail."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = "test-api-key"
            
            # Mock both providers failing
            summarization_service.ollama_client = Mock()
            summarization_service.ollama_client.post = AsyncMock(side_effect=LLMError("Ollama failed"))
            
            summarization_service.claude_client = Mock()
            summarization_service.claude_client.post = AsyncMock(side_effect=LLMError("Claude failed"))
            
            with pytest.raises(LLMError, match="All summarization providers failed"):
                await summarization_service.summarize_content(sample_summarization_request)

    @pytest.mark.asyncio
    async def test_batch_summarize_success(self, summarization_service, sample_ollama_response):
        """Test batch summarization."""
        requests = [
            SummarizationRequest(content=f"Article {i} content about technology", max_length=100)
            for i in range(3)
        ]
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.json.return_value = sample_ollama_response
        mock_response.raise_for_status = Mock()
        
        summarization_service.ollama_client = Mock()
        summarization_service.ollama_client.post = AsyncMock(return_value=mock_response)
        
        results = await summarization_service.batch_summarize(requests, max_concurrent=2)
        
        assert len(results) == 3
        assert all(isinstance(result, ArticleSummary) for result in results)
        assert summarization_service.ollama_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_summarize_partial_failure(self, summarization_service, sample_ollama_response):
        """Test batch summarization with some failures."""
        requests = [
            SummarizationRequest(content=f"Article {i} content", max_length=100)
            for i in range(3)
        ]
        
        # Mock mixed responses (success, failure, success)
        responses = [
            Mock(),  # Success
            Exception("Failed"),  # Failure
            Mock()   # Success
        ]
        
        responses[0].json.return_value = sample_ollama_response
        responses[0].raise_for_status = Mock()
        responses[2].json.return_value = sample_ollama_response
        responses[2].raise_for_status = Mock()
        
        summarization_service.ollama_client = Mock()
        summarization_service.ollama_client.post = AsyncMock(side_effect=responses)
        
        results = await summarization_service.batch_summarize(requests)
        
        # Should have 2 successful results
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) == 2

    @pytest.mark.asyncio
    async def test_health_check_all_providers(self, summarization_service):
        """Test health check with all providers available."""
        # Mock successful initialization
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = "test-api-key"
            
            await summarization_service.initialize()
            
            health = await summarization_service.health_check()
            
            assert health["status"] == "healthy"
            assert health["providers"]["ollama"] == "available"
            assert health["providers"]["claude"] == "available"

    @pytest.mark.asyncio
    async def test_health_check_no_providers(self, summarization_service):
        """Test health check with no providers configured."""
        health = await summarization_service.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["providers"]["ollama"] == "not_configured"
        assert health["providers"]["claude"] == "not_configured"

    @pytest.mark.asyncio
    async def test_auto_initialization(self, summarization_service, sample_summarization_request, sample_ollama_response):
        """Test automatic initialization during summarization."""
        with patch('src.services.summarization_service.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://localhost:11434"
            mock_settings.claude_api_key = None
            
            # Mock Ollama response
            mock_response = Mock()
            mock_response.json.return_value = sample_ollama_response
            mock_response.raise_for_status = Mock()
            
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = Mock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client
                
                # Service should auto-initialize
                result = await summarization_service.summarize_content(sample_summarization_request)
                
                assert isinstance(result, ArticleSummary)
                mock_client_class.assert_called_once()
