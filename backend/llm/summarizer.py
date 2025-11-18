"""
Article Summarizer for AI Tech News Assistant
============================================

Main summarizer class that orchestrates different LLM providers
and provides a unified interface for article summarization.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from .providers import LLMProvider, OllamaProvider, ClaudeProvider
from .groq_provider import GroqProvider
from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class LLMProviderType(Enum):
    """Supported LLM provider types."""
    OLLAMA = "ollama"
    CLAUDE = "claude"
    GROQ = "groq"
    AUTO = "auto"  # Automatically select best available provider


class ArticleSummarizer:
    """
    Main summarizer class that handles article summarization using various LLM providers.
    
    Features:
    - Multiple provider support (Ollama, Claude)
    - Automatic fallback to available providers
    - Caching and rate limiting (future)
    - Structured output with metadata
    """
    
    def __init__(self):
        """Initialize the summarizer with available providers."""
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = LLMProviderType.AUTO
        
        # Initialize providers
        self._initialize_providers()
        logger.info(f"Article summarizer initialized with {len(self.providers)} providers")
    
    def _initialize_providers(self) -> None:
        """Initialize and test available LLM providers."""
        # Initialize Groq provider (prioritize - fastest and free)
        try:
            if hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY:
                groq = GroqProvider(
                    api_key=settings.GROQ_API_KEY,
                    model=getattr(settings, 'GROQ_MODEL', 'llama-3.2-3b-preview'),
                    timeout=getattr(settings, 'LLM_TIMEOUT', 60)
                )
                self.providers[LLMProviderType.GROQ.value] = groq
                logger.info("Groq provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq provider: {str(e)}")
        
        # Initialize Ollama provider
        try:
            ollama = OllamaProvider(
                model=getattr(settings, 'OLLAMA_MODEL', 'llama2')
            )
            self.providers[LLMProviderType.OLLAMA.value] = ollama
            logger.info("Ollama provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {str(e)}")
        
        # Initialize Claude provider
        try:
            claude = ClaudeProvider()
            self.providers[LLMProviderType.CLAUDE.value] = claude
            logger.info("Claude provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Claude provider: {str(e)}")
    
    async def get_available_providers(self) -> List[str]:
        """
        Get list of currently available providers.
        
        Returns:
            List of available provider names
        """
        available = []
        
        for name, provider in self.providers.items():
            try:
                if await provider.is_available():
                    available.append(name)
                    logger.debug(f"Provider {name} is available")
                else:
                    logger.debug(f"Provider {name} is not available")
            except Exception as e:
                logger.warning(f"Error checking provider {name}: {str(e)}")
        
        logger.info(f"Available providers: {available}")
        return available
    
    async def summarize_article(self, 
                              article_text: str,
                              title: Optional[str] = None,
                              provider: LLMProviderType = LLMProviderType.AUTO,
                              **kwargs) -> Dict[str, Any]:
        """
        Summarize an article using the specified or best available provider.
        
        Args:
            article_text: The article content to summarize
            title: Optional article title for context
            provider: Preferred provider (auto-selects if AUTO)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict containing:
            - summary: The generated summary
            - keywords: Extracted keywords
            - title: Original or provided title
            - provider: Provider used
            - model: Model used
            - metadata: Additional metadata
        """
        if not article_text or len(article_text.strip()) < 50:
            raise ValueError("Article text is too short to summarize")
        
        # Select provider
        selected_provider = await self._select_provider(provider)
        if not selected_provider:
            raise Exception("No LLM providers are currently available")
        
        try:
            logger.info(f"Summarizing article using {selected_provider}")
            
            # Prepare text for summarization
            text_to_summarize = self._prepare_text(article_text, title)
            
            # Get summarization from provider
            provider_instance = self.providers[selected_provider]
            result = await provider_instance.summarize(text_to_summarize, **kwargs)
            
            # Enhance result with additional metadata
            enhanced_result = {
                **result,
                "title": title,
                "original_length": len(article_text),
                "summary_length": len(result.get("summary", "")),
                "compression_ratio": round(len(result.get("summary", "")) / len(article_text), 3)
            }
            
            logger.info(f"Successfully summarized article (compression: {enhanced_result['compression_ratio']})")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error summarizing with {selected_provider}: {str(e)}")
            
            # Try fallback if auto mode
            if provider == LLMProviderType.AUTO:
                return await self._try_fallback_providers(text_to_summarize, selected_provider, **kwargs)
            else:
                raise e
    
    async def _select_provider(self, preferred: LLMProviderType) -> Optional[str]:
        """
        Select the best available provider based on preference and availability.
        
        Args:
            preferred: Preferred provider type
            
        Returns:
            Provider name or None if none available
        """
        if preferred != LLMProviderType.AUTO:
            # Check if specific provider is available
            provider_name = preferred.value
            if (provider_name in self.providers and 
                await self.providers[provider_name].is_available()):
                return provider_name
            else:
                logger.warning(f"Requested provider {provider_name} is not available")
                return None
        
        # Auto mode: select best available provider
        available_providers = await self.get_available_providers()
        
        if not available_providers:
            return None
        
        # Preference order: Claude (more accurate) -> Ollama (local/free)
        provider_priority = [LLMProviderType.CLAUDE.value, LLMProviderType.OLLAMA.value]
        
        for preferred_provider in provider_priority:
            if preferred_provider in available_providers:
                logger.info(f"Auto-selected provider: {preferred_provider}")
                return preferred_provider
        
        # Fallback to first available
        selected = available_providers[0]
        logger.info(f"Using fallback provider: {selected}")
        return selected
    
    async def _try_fallback_providers(self, 
                                    text: str, 
                                    failed_provider: str,
                                    **kwargs) -> Dict[str, Any]:
        """Try other available providers as fallback."""
        available_providers = await self.get_available_providers()
        fallback_providers = [p for p in available_providers if p != failed_provider]
        
        for provider_name in fallback_providers:
            try:
                logger.info(f"Trying fallback provider: {provider_name}")
                provider = self.providers[provider_name]
                result = await provider.summarize(text, **kwargs)
                
                logger.info(f"Successfully used fallback provider: {provider_name}")
                return result
                
            except Exception as e:
                logger.warning(f"Fallback provider {provider_name} also failed: {str(e)}")
                continue
        
        raise Exception("All available providers failed to generate summary")
    
    def _prepare_text(self, article_text: str, title: Optional[str] = None) -> str:
        """
        Prepare article text for summarization.
        
        Args:
            article_text: Raw article content
            title: Optional article title
            
        Returns:
            Prepared text for summarization
        """
        # Clean and prepare text
        text = article_text.strip()
        
        # Add title context if provided
        if title:
            text = f"Title: {title}\n\nContent:\n{text}"
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
        text = re.sub(r'[ \t]+', ' ', text)      # Normalize spaces
        
        return text
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status information about all providers.
        
        Returns:
            Dict with provider status and capabilities
        """
        status = {
            "providers": {},
            "available_count": 0,
            "default_provider": self.default_provider.value
        }
        
        for name, provider in self.providers.items():
            try:
                is_available = await provider.is_available()
                status["providers"][name] = {
                    "available": is_available,
                    "type": name,
                    "model": getattr(provider, 'model', 'unknown')
                }
                if is_available:
                    status["available_count"] += 1
                    
            except Exception as e:
                status["providers"][name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return status
