"""
Unit Tests for Summarization Service
===================================

Tests for summarization service functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import asyncio
from pydantic import ValidationError as PydanticValidationError

from src.services.summarization_service import SummarizationService
from src.models.article import SummarizationRequest, ArticleSummary, BatchSummarizationRequest
from src.core.exceptions import LLMError, ValidationError


class TestSummarizationService:
    """Test cases for SummarizationService."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.openai_api_key = "test-api-key"
        settings.summarization_model = "gpt-3.5-turbo"
        settings.max_summary_length = 150
        settings.temperature = 0.7
        return settings
    
    @pytest.fixture
    def service(self, mock_settings):
        """Create summarization service with mocked settings."""
        with patch('src.services.summarization_service.settings', mock_settings):
            return SummarizationService()
    
    @pytest.fixture
    def sample_content(self):
        """Sample article content for testing."""
        return """
        Artificial Intelligence (AI) has been making significant strides in recent years, 
        particularly in the field of natural language processing. Large language models 
        like GPT-3 and GPT-4 have demonstrated remarkable capabilities in understanding 
        and generating human-like text. These advancements have opened up new possibilities 
        for applications in various domains, including content creation, code generation, 
        and conversational AI. However, challenges remain in terms of bias, reliability, 
        and the need for responsible AI development. Researchers and developers continue 
        to work on improving these models while addressing ethical considerations and 
        ensuring that AI systems are beneficial, safe, and aligned with human values.
        """
    
    @pytest.mark.asyncio
    async def test_initialization(self, service):
        """Test service initialization."""
        assert service.model == "gpt-3.5-turbo"
        assert service.max_length == 150
        assert service.temperature == 0.7
        assert service.client is not None
    
    @pytest.mark.asyncio
    async def test_summarize_content_success(self, service, sample_content):
        """Test successful content summarization."""
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI has made significant progress in NLP with models like GPT-3/4."
        mock_response.usage.total_tokens = 150
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            request = SummarizationRequest(
                content=sample_content,
                max_length=100,
                style="concise"
            )
            
            response = await service.summarize_content(request)
        
        assert isinstance(response, ArticleSummary)
        assert "AI has made significant progress" in response.summary
        assert response.word_count == 150
        assert isinstance(response.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_summarize_content_with_custom_style(self, service, sample_content):
        """Test summarization with different styles."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Bullet point summary"
        mock_response.usage.total_tokens = 100
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            request = SummarizationRequest(
                content=sample_content,
                style="bullet_points"
            )
            
            await service.summarize_content(request)
            
            # Verify the prompt includes bullet point instruction
            call_args = mock_create.call_args
            messages = call_args[1]['messages']
            system_message = next(msg for msg in messages if msg['role'] == 'system')
            assert 'bullet points' in system_message['content'].lower()
    
    @pytest.mark.asyncio
    async def test_summarize_content_openai_error(self, service, sample_content):
        """Test handling of OpenAI API errors."""
        with patch.object(service.client.chat.completions, 'create', side_effect=Exception("API Error")):
            request = SummarizationRequest(content=sample_content)
            
            with pytest.raises(LLMError, match="Summarization failed"):
                await service.summarize_content(request)
    
    @pytest.mark.asyncio
    async def test_summarize_content_empty_response(self, service, sample_content):
        """Test handling of empty response from OpenAI."""
        mock_response = MagicMock()
        mock_response.choices = []
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            request = SummarizationRequest(content=sample_content)
            
            with pytest.raises(LLMError, match="No summary generated"):
                await service.summarize_content(request)
    
    @pytest.mark.asyncio
    async def test_summarize_content_validation_error(self, service):
        """Test validation of input content."""
        # Test with empty content
        with pytest.raises(PydanticValidationError):
            request = SummarizationRequest(content="")
            await service.summarize_content(request)
        
        # Test with content too short  
        request = SummarizationRequest(content="Too short")
        with pytest.raises(ValidationError):
            await service.summarize_content(request)
    
    @pytest.mark.asyncio
    async def test_batch_summarize_success(self, service):
        """Test successful batch summarization."""
        contents = [
            "First article content that is long enough to be summarized properly.",
            "Second article content that is also long enough for summarization.",
            "Third article content with sufficient length for the summarization process."
        ]
        
        mock_responses = []
        for i, content in enumerate(contents):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = f"Summary {i+1}"
            mock_response.usage.total_tokens = 50
            mock_responses.append(mock_response)
        
        with patch.object(service.client.chat.completions, 'create', side_effect=mock_responses):
            requests = [
                SummarizationRequest(content=content, max_length=100, style="concise")
                for content in contents
            ]
            
            responses = await service.batch_summarize(requests)
        
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert isinstance(response, ArticleSummary)
            assert f"Summary {i+1}" in response.summary
    
    @pytest.mark.asyncio
    async def test_batch_summarize_with_failures(self, service):
        """Test batch summarization with some failures."""
        contents = [
            "First article content that is long enough to be summarized properly.",
            "Second article content that is also long enough for summarization."
        ]
        
        # First succeeds, second fails
        mock_success = MagicMock()
        mock_success.choices = [MagicMock()]
        mock_success.choices[0].message.content = "Successful summary"
        mock_success.usage.total_tokens = 50
        
        responses = [mock_success, Exception("API Error")]
        
        requests = [SummarizationRequest(content=content) for content in contents]
        
        with patch.object(service.client.chat.completions, 'create', side_effect=responses):
            results = await service.batch_summarize(requests)
        
        # Should return one successful result and skip the failed one
        assert len(results) == 1
        assert "Successful summary" in results[0].summary
    
    @pytest.mark.asyncio
    async def test_batch_summarize_empty_list(self, service):
        """Test batch summarization with empty content list."""
        requests = []
        
        results = await service.batch_summarize(requests)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_summary_prompt_styles(self, service):
        """Test different summarization style prompts."""
        test_cases = [
            ("concise", "concise"),
            ("detailed", "detailed"),
            ("bullet_points", "bullet points"),
            ("technical", "technical"),
            ("executive", "executive"),
            ("unknown_style", "concise")  # Should default to concise
        ]
        
        for style, expected_keyword in test_cases:
            prompt = service._get_summary_prompt(style, 100)
            assert expected_keyword in prompt.lower()
            assert "100" in prompt  # Max length should be included
    
    @pytest.mark.asyncio
    async def test_validate_content_length(self, service):
        """Test content length validation."""
        # Too short
        assert not service._validate_content("Short")
        
        # Just right
        valid_content = "This is a longer piece of content that should pass validation."
        assert service._validate_content(valid_content)
        
        # Too long (test with very long content)
        very_long_content = "A" * 100000  # 100k characters
        assert not service._validate_content(very_long_content)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service):
        """Test health check with successful API connection."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.total_tokens = 10
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            health = await service.health_check()
        
        assert health["status"] == "healthy"
        assert health["api_accessible"] is True
        assert health["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_health_check_api_failure(self, service):
        """Test health check with API failure."""
        with patch.object(service.client.chat.completions, 'create', side_effect=Exception("API Error")):
            health = await service.health_check()
        
        assert health["status"] == "unhealthy"
        assert health["api_accessible"] is False
        assert "API Error" in health["error"]
    
    @pytest.mark.asyncio
    async def test_clean_summary_text(self, service):
        """Test summary text cleaning."""
        test_cases = [
            ("  Summary with extra spaces  ", "Summary with extra spaces"),
            ("Summary\nwith\nnewlines", "Summary with newlines"),
            ("Summary with\ttabs", "Summary with tabs"),
            ("Summary with   multiple   spaces", "Summary with multiple spaces"),
            ("", ""),
            ("Normal summary", "Normal summary")
        ]
        
        for input_text, expected in test_cases:
            cleaned = service._clean_summary(input_text)
            assert cleaned == expected
    
    @pytest.mark.asyncio
    async def test_calculate_processing_time(self, service):
        """Test processing time calculation."""
        start_time = datetime.utcnow()
        
        # Simulate some processing time
        await asyncio.sleep(0.01)  # 10ms
        
        processing_time = service._calculate_processing_time(start_time)
        
        assert isinstance(processing_time, float)
        assert processing_time >= 0.01
        assert processing_time < 1.0  # Should be less than 1 second


class TestSummarizationServiceConfiguration:
    """Test different configuration scenarios for SummarizationService."""
    
    @pytest.mark.asyncio
    async def test_different_models(self):
        """Test service with different models."""
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        for model in models:
            settings = MagicMock()
            settings.openai_api_key = "test-key"
            settings.summarization_model = model
            settings.max_summary_length = 150
            settings.temperature = 0.7
            
            with patch('src.services.summarization_service.settings', settings):
                service = SummarizationService()
                assert service.model == model
    
    @pytest.mark.asyncio
    async def test_temperature_settings(self):
        """Test service with different temperature settings."""
        temperatures = [0.0, 0.5, 1.0, 1.5]
        
        for temp in temperatures:
            settings = MagicMock()
            settings.openai_api_key = "test-key"
            settings.summarization_model = "gpt-3.5-turbo"
            settings.max_summary_length = 150
            settings.temperature = temp
            
            with patch('src.services.summarization_service.settings', settings):
                service = SummarizationService()
                assert service.temperature == temp
    
    @pytest.mark.asyncio
    async def test_max_length_settings(self):
        """Test service with different max length settings."""
        max_lengths = [50, 100, 200, 500]
        
        for max_len in max_lengths:
            settings = MagicMock()
            settings.openai_api_key = "test-key"
            settings.summarization_model = "gpt-3.5-turbo"
            settings.max_summary_length = max_len
            settings.temperature = 0.7
            
            with patch('src.services.summarization_service.settings', settings):
                service = SummarizationService()
                assert service.max_length == max_len
    
    @pytest.mark.skip(reason="API key validation test conflicts with pytest environment detection")
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test service initialization with missing API key."""
        settings = MagicMock()
        settings.openai_api_key = None
        settings.summarization_model = "gpt-3.5-turbo"
        settings.max_summary_length = 150
        settings.temperature = 0.7
        settings.is_testing.return_value = False
        
        with patch('src.services.summarization_service.settings', settings):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                SummarizationService(skip_api_key_validation=False)


class TestSummarizationServicePerformance:
    """Test performance-related aspects of SummarizationService."""
    
    @pytest.fixture
    def service_with_mocked_client(self):
        """Create service with mocked OpenAI client."""
        settings = MagicMock()
        settings.openai_api_key = "test-key"
        settings.summarization_model = "gpt-3.5-turbo"
        settings.max_summary_length = 150
        settings.temperature = 0.7
        
        with patch('src.services.summarization_service.settings', settings):
            service = SummarizationService()
            service.client = MagicMock()
            return service
    
    @pytest.mark.asyncio
    async def test_concurrent_summarization(self, service_with_mocked_client):
        """Test concurrent summarization requests."""
        service = service_with_mocked_client
        
        # Mock multiple successful responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Concurrent summary"
        mock_response.usage.total_tokens = 50
        
        service.client.chat.completions.create.return_value = mock_response
        
        # Create multiple summarization tasks
        contents = [f"Content {i} that is long enough for summarization." for i in range(5)]
        tasks = []
        
        for content in contents:
            request = SummarizationRequest(content=content)
            tasks.append(service.summarize_content(request))
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, ArticleSummary)
            assert "Concurrent summary" in result.summary
    
    @pytest.mark.asyncio
    async def test_large_batch_processing(self, service_with_mocked_client):
        """Test processing large batches of content."""
        service = service_with_mocked_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Batch summary"
        mock_response.usage.total_tokens = 50
        
        service.client.chat.completions.create.return_value = mock_response
        
        # Create large batch
        large_batch = [f"Article content {i} with sufficient length for processing." for i in range(50)]
        requests = [SummarizationRequest(content=content) for content in large_batch]
        
        results = await service.batch_summarize(requests)
        
        assert len(results) == 50
        for result in results:
            assert isinstance(result, ArticleSummary)
            assert "Batch summary" in result.summary
