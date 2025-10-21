"""
LLM Service Factory
==================

Factory for creating and managing LLM providers.
Automatically selects the best available provider based on configuration.
"""

from typing import Optional, Dict, Any
from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


async def get_llm_provider():
    """
    Get the configured LLM provider with automatic fallback.
    
    Priority order (unless overridden by LLM_PROVIDER env var):
    1. Groq (if API key available) - Fast, free, cloud-based
    2. Ollama (if running locally) - Free, local inference
    3. Claude (if API key available) - High quality
    4. None - Returns mock provider
    
    Returns:
        LLM provider instance
    """
    # Check explicit provider selection
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "groq":
        if settings.groq_api_key:
            logger.info("Using Groq provider (configured)")
            from llm.groq_provider import GroqProvider
            return GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout=settings.llm_timeout
            )
        else:
            logger.warning("Groq selected but API key not configured, falling back")
    
    elif provider_name == "ollama":
        logger.info("Using Ollama provider (configured)")
        from llm.providers import OllamaProvider
        provider = OllamaProvider(
            base_url=settings.ollama_host,
            model=settings.ollama_model
        )
        # Check if available
        if await provider.is_available():
            return provider
        else:
            logger.warning("Ollama not available, falling back")
    
    elif provider_name == "claude":
        if settings.anthropic_api_key:
            logger.info("Using Claude provider (configured)")
            from llm.providers import ClaudeProvider
            return ClaudeProvider(
                api_key=settings.anthropic_api_key
            )
        else:
            logger.warning("Claude selected but API key not configured, falling back")
    
    # Auto-detect: Try providers in order of preference
    logger.info("Auto-detecting best available LLM provider...")
    
    # 1. Try Groq (best for production - fast, free, cloud)
    if settings.groq_api_key:
        try:
            from llm.groq_provider import GroqProvider
            provider = GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                timeout=settings.llm_timeout
            )
            if await provider.is_available():
                logger.info("✅ Using Groq provider (auto-detected)")
                return provider
        except Exception as e:
            logger.warning(f"Groq provider failed: {e}")
    
    # 2. Try Ollama (good for local development)
    try:
        from llm.providers import OllamaProvider
        provider = OllamaProvider(
            base_url=settings.ollama_host,
            model=settings.ollama_model
        )
        if await provider.is_available():
            logger.info("✅ Using Ollama provider (auto-detected)")
            return provider
    except Exception as e:
        logger.warning(f"Ollama provider failed: {e}")
    
    # 3. Try Claude (high quality, but costs money)
    if settings.anthropic_api_key:
        try:
            from llm.providers import ClaudeProvider
            provider = ClaudeProvider(api_key=settings.anthropic_api_key)
            if await provider.is_available():
                logger.info("✅ Using Claude provider (auto-detected)")
                return provider
        except Exception as e:
            logger.warning(f"Claude provider failed: {e}")
    
    # 4. No provider available - return mock
    logger.warning("⚠️  No LLM provider available, using mock provider")
    return MockProvider()


class MockProvider:
    """Mock LLM provider for when no real provider is available."""
    
    async def is_available(self) -> bool:
        return True
    
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        """Return a mock summary."""
        return {
            "success": True,
            "summary": "This is a mock summary. Configure an LLM provider (Groq recommended) to get real summaries.",
            "keywords": ["mock", "demo", "placeholder"],
            "model": "mock",
            "provider": "mock"
        }
    
    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Return a mock chat response."""
        return {
            "success": True,
            "response": "This is a mock response. Configure an LLM provider (Groq recommended) to enable AI chat.",
            "model": "mock",
            "provider": "mock"
        }
