"""
Summarization Service
==================

Business logic for LLM-based text summarization using multiple providers.
Handles provider fallback, prompt optimization, and response processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import httpx

from ..core.config import get_settings

settings = get_settings()
from ..core.exceptions import LLMError, ValidationError
from ..models.article import (
    SummarizationRequest,
    ArticleSummary
)

logger = logging.getLogger(__name__)


class SummarizationService:
    """
    Service for handling LLM-based text summarization.
    
    This service manages multiple LLM providers (Ollama, Claude API),
    implements provider fallback, and provides optimized prompts
    for high-quality summarization.
    """
    
    def __init__(self):
        """Initialize the summarization service."""
        self.ollama_client = None
        self.claude_client = None
        self.max_content_length = 50000  # Max content length for processing
        self.request_timeout = 120.0     # 2 minutes for LLM requests
        
    async def initialize(self) -> None:
        """Initialize HTTP clients for LLM providers."""
        # Initialize Ollama client
        if settings.ollama_base_url:
            self.ollama_client = httpx.AsyncClient(
                base_url=settings.ollama_base_url,
                timeout=self.request_timeout
            )
        
        # Initialize Claude client
        if settings.claude_api_key:
            self.claude_client = httpx.AsyncClient(
                timeout=self.request_timeout,
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            )
        
        logger.info("Summarization service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.ollama_client:
            await self.ollama_client.aclose()
            self.ollama_client = None
        
        if self.claude_client:
            await self.claude_client.aclose()
            self.claude_client = None
        
        logger.info("Summarization service cleaned up")
    
    async def summarize_content(self, request: SummarizationRequest) -> ArticleSummary:
        """
        Generate a summary for the provided content.
        
        Args:
            request: Summarization request with content and parameters
            
        Returns:
            ArticleSummary with generated summary
            
        Raises:
            LLMError: If summarization fails with all providers
            ValidationError: If request validation fails
        """
        if not self.ollama_client and not self.claude_client:
            await self.initialize()
        
        # Validate request
        self._validate_request(request)
        
        # Prepare content for summarization
        content = self._prepare_content(request.content)
        
        # Try providers in order with fallback
        providers = []
        if self.ollama_client and settings.ollama_model:
            providers.append(('ollama', self._summarize_with_ollama))
        if self.claude_client:
            providers.append(('claude', self._summarize_with_claude))
        
        if not providers:
            raise LLMError("No LLM providers available")
        
        last_error = None
        for provider_name, provider_func in providers:
            try:
                logger.info(f"Attempting summarization with {provider_name}")
                
                summary_text = await provider_func(content, request)
                
                return ArticleSummary(
                    summary=summary_text,
                    provider=provider_name,
                    model=settings.ollama_model if provider_name == 'ollama' else 'claude-3-sonnet',
                    content_length=len(request.content),
                    summary_length=len(summary_text),
                    generated_at=datetime.utcnow()
                )
                
            except Exception as e:
                logger.warning(f"Summarization failed with {provider_name}: {e}")
                last_error = e
                continue
        
        # All providers failed
        error_msg = f"All summarization providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise LLMError(error_msg)
    
    def _validate_request(self, request: SummarizationRequest) -> None:
        """Validate summarization request."""
        if not request.content or not request.content.strip():
            raise ValidationError("Content cannot be empty")
        
        if len(request.content) < 100:
            raise ValidationError("Content too short for meaningful summarization (min 100 chars)")
        
        if len(request.content) > self.max_content_length:
            raise ValidationError(f"Content too long (max {self.max_content_length} chars)")
        
        if request.max_length and request.max_length < 50:
            raise ValidationError("Maximum summary length too short (min 50 chars)")
    
    def _prepare_content(self, content: str) -> str:
        """Prepare and clean content for summarization."""
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Truncate if too long (with some buffer for prompt)
        if len(content) > self.max_content_length - 1000:
            content = content[:self.max_content_length - 1000] + "..."
        
        return content
    
    async def _summarize_with_ollama(
        self, 
        content: str, 
        request: SummarizationRequest
    ) -> str:
        """
        Generate summary using Ollama local LLM.
        
        Args:
            content: Content to summarize
            request: Original summarization request
            
        Returns:
            Generated summary text
            
        Raises:
            LLMError: If Ollama request fails
        """
        prompt = self._build_summarization_prompt(content, request)
        
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": request.max_length or 500
            }
        }
        
        try:
            response = await self.ollama_client.post("/api/generate", json=payload)
            response.raise_for_status()
            
            result = response.json()
            summary = result.get("response", "").strip()
            
            if not summary:
                raise LLMError("Ollama returned empty response")
            
            return self._post_process_summary(summary)
            
        except httpx.TimeoutException:
            raise LLMError("Ollama request timed out")
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Ollama HTTP error: {e.response.status_code}")
        except Exception as e:
            raise LLMError(f"Ollama request failed: {str(e)}")
    
    async def _summarize_with_claude(
        self, 
        content: str, 
        request: SummarizationRequest
    ) -> str:
        """
        Generate summary using Claude API.
        
        Args:
            content: Content to summarize
            request: Original summarization request
            
        Returns:
            Generated summary text
            
        Raises:
            LLMError: If Claude request fails
        """
        prompt = self._build_summarization_prompt(content, request)
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": request.max_length or 500,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = await self.claude_client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("content"):
                raise LLMError("Claude returned empty response")
            
            summary = result["content"][0]["text"].strip()
            return self._post_process_summary(summary)
            
        except httpx.TimeoutException:
            raise LLMError("Claude request timed out")
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", "")
            except:
                pass
            raise LLMError(f"Claude HTTP error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise LLMError(f"Claude request failed: {str(e)}")
    
    def _build_summarization_prompt(
        self, 
        content: str, 
        request: SummarizationRequest
    ) -> str:
        """
        Build an optimized prompt for summarization.
        
        Args:
            content: Content to summarize
            request: Summarization request with parameters
            
        Returns:
            Formatted prompt for LLM
        """
        # Determine summary style based on request
        style_instruction = ""
        if request.style == "bullet_points":
            style_instruction = "Format the summary as clear bullet points."
        elif request.style == "paragraph":
            style_instruction = "Format the summary as a coherent paragraph."
        else:
            style_instruction = "Format the summary in the most appropriate style."
        
        # Build length instruction
        length_instruction = ""
        if request.max_length:
            words_estimate = request.max_length // 5  # Rough chars to words conversion
            length_instruction = f"Keep the summary under {words_estimate} words."
        
        prompt = f"""
Please provide a concise and accurate summary of the following content. Focus on the main points, key insights, and important details.

{style_instruction}
{length_instruction}

Content to summarize:
{content}

Summary:"""
        
        return prompt.strip()
    
    def _post_process_summary(self, summary: str) -> str:
        """
        Post-process the generated summary for quality and consistency.
        
        Args:
            summary: Raw summary from LLM
            
        Returns:
            Cleaned and processed summary
        """
        # Remove common LLM artifacts
        summary = summary.strip()
        
        # Remove phrases like "Here's a summary:" or "Summary:"
        prefixes_to_remove = [
            "Here's a summary:",
            "Here is a summary:",
            "Summary:",
            "The summary is:",
            "This article discusses:",
        ]
        
        for prefix in prefixes_to_remove:
            if summary.lower().startswith(prefix.lower()):
                summary = summary[len(prefix):].strip()
        
        # Ensure proper sentence ending
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        return summary
    
    async def batch_summarize(
        self, 
        requests: List[SummarizationRequest]
    ) -> List[ArticleSummary]:
        """
        Generate summaries for multiple content pieces.
        
        Args:
            requests: List of summarization requests
            
        Returns:
            List of generated summaries
        """
        if len(requests) > 10:
            raise ValidationError("Too many requests for batch processing (max 10)")
        
        # Process with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
        async def process_single(req):
            async with semaphore:
                try:
                    return await self.summarize_content(req)
                except Exception as e:
                    logger.error(f"Batch summarization failed for item: {e}")
                    return None
        
        tasks = [process_single(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed results
        summaries = []
        for result in results:
            if isinstance(result, ArticleSummary):
                summaries.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Batch item failed: {result}")
        
        return summaries
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the summarization service.
        
        Returns:
            Dictionary with health status information
        """
        if not self.ollama_client and not self.claude_client:
            await self.initialize()
        
        status = {
            "status": "healthy",
            "providers": {}
        }
        
        # Test Ollama if configured
        if self.ollama_client:
            try:
                response = await self.ollama_client.get("/api/tags", timeout=5.0)
                if response.status_code == 200:
                    status["providers"]["ollama"] = {
                        "status": "available",
                        "model": settings.ollama_model
                    }
                else:
                    status["providers"]["ollama"] = {
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                status["providers"]["ollama"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Test Claude if configured
        if self.claude_client:
            status["providers"]["claude"] = {
                "status": "configured",
                "note": "API key present"
            }
        
        # Overall status
        if not status["providers"]:
            status["status"] = "unhealthy"
            status["error"] = "No providers available"
        
        return status
