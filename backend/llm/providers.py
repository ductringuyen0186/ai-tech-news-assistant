"""
LLM Providers for AI Tech News Assistant
=======================================

This module contains implementations for different LLM providers:
- OllamaProvider: Local LLM inference using Ollama
- ClaudeProvider: Anthropic Claude API integration
"""

import httpx
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """Summarize text and return structured response."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLM inference.
    
    Supports various models like Llama2, Mistral, CodeLlama, etc.
    Requires Ollama to be installed and running locally.
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "llama2",
                 timeout: int = 60):
        """
        Initialize Ollama provider.
        
        Args:
            base_url: Ollama server URL
            model: Model name to use (llama2, mistral, etc.)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        logger.info(f"Initialized Ollama provider with model: {model}")
    
    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    logger.warning("Ollama server not responding")
                    return False
                
                # Check if our model is available
                models = response.json()
                available_models = [m["name"] for m in models.get("models", [])]
                
                if self.model not in available_models:
                    logger.warning(f"Model {self.model} not found. Available: {available_models}")
                    return False
                
                logger.info(f"Ollama is available with model: {self.model}")
                return True
                
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
    
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Summarize text using Ollama.
        
        Args:
            text: Article text to summarize
            **kwargs: Additional parameters
            
        Returns:
            Dict with summary, keywords, and metadata
        """
        try:
            # Create summarization prompt
            prompt = self._create_summary_prompt(text)
            
            # Make request to Ollama
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 200
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama request failed: {response.status_code}")
                
                result = response.json()
                summary_text = result.get("response", "").strip()
                
                # Extract keywords from summary
                keywords = await self._extract_keywords(summary_text)
                
                return {
                    "summary": summary_text,
                    "keywords": keywords,
                    "model": self.model,
                    "provider": "ollama",
                    "confidence": 0.8  # Placeholder confidence score
                }
                
        except Exception as e:
            logger.error(f"Error in Ollama summarization: {str(e)}")
            raise Exception(f"Ollama summarization failed: {str(e)}")
    
    def _create_summary_prompt(self, text: str) -> str:
        """Create a well-structured prompt for summarization."""
        return f"""You are an AI assistant specialized in summarizing technology news articles. 

Please provide a concise, informative summary of the following article in 3-5 sentences. Focus on:
- The main topic or announcement
- Key technical details or implications
- Important companies, people, or products mentioned
- The significance or impact of the news

Article text:
{text[:4000]}  # Limit text to avoid token limits

Summary:"""
    
    async def _extract_keywords(self, summary: str) -> List[str]:
        """Extract keywords from the summary text."""
        # Simple keyword extraction (can be enhanced with NLP)
        import re
        
        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }
        
        # Extract words (alphanumeric, 3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', summary.lower())
        keywords = [w for w in words if w not in common_words]
        
        # Return top 5 unique keywords
        return list(dict.fromkeys(keywords))[:5]


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude provider for cloud-based summarization.
    
    Requires ANTHROPIC_API_KEY environment variable.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "claude-3-haiku-20240307",
                 timeout: int = 30):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key (will use env var if not provided)
            model: Claude model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1"
        
        if not self.api_key:
            logger.warning("No Anthropic API key provided - Claude will not be available")
        else:
            logger.info(f"Initialized Claude provider with model: {model}")
    
    async def is_available(self) -> bool:
        """Check if Claude API is available."""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"x-api-key": self.api_key}
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error checking Claude availability: {str(e)}")
            return False
    
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Summarize text using Claude.
        
        Args:
            text: Article text to summarize
            **kwargs: Additional parameters
            
        Returns:
            Dict with summary, keywords, and metadata
        """
        if not self.api_key:
            raise Exception("Claude API key not configured")
        
        try:
            prompt = self._create_summary_prompt(text)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 300,
                        "temperature": 0.3,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Claude request failed: {response.status_code}")
                
                result = response.json()
                summary_text = result["content"][0]["text"].strip()
                
                # Extract keywords from summary
                keywords = await self._extract_keywords(summary_text)
                
                return {
                    "summary": summary_text,
                    "keywords": keywords,
                    "model": self.model,
                    "provider": "claude",
                    "confidence": 0.9  # Higher confidence for Claude
                }
                
        except Exception as e:
            logger.error(f"Error in Claude summarization: {str(e)}")
            raise Exception(f"Claude summarization failed: {str(e)}")
    
    def _create_summary_prompt(self, text: str) -> str:
        """Create a well-structured prompt for Claude."""
        return f"""Please provide a concise, informative summary of this technology news article in exactly 3-5 sentences.

Focus on:
- The main announcement or development
- Key technical details and implications  
- Important companies, people, or technologies involved
- The significance or potential impact

Article:
{text[:8000]}  # Claude can handle more text

Provide only the summary, no additional commentary."""
    
    async def _extract_keywords(self, summary: str) -> List[str]:
        """Extract keywords from the summary text."""
        # Same implementation as Ollama for consistency
        import re
        
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', summary.lower())
        keywords = [w for w in words if w not in common_words]
        
        return list(dict.fromkeys(keywords))[:5]
