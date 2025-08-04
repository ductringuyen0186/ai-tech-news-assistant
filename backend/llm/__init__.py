"""
LLM Integration Module for AI Tech News Assistant
================================================

This module handles integration with various LLM providers including:
- Ollama (local LLM inference)
- Anthropic Claude
- Extensible interface for other providers

Features:
- Multiple provider support with automatic fallback
- Article summarization with structured output
- Keyword extraction and metadata generation
- Provider health checking and status monitoring
"""

from .summarizer import ArticleSummarizer, LLMProviderType
from .providers import LLMProvider, OllamaProvider, ClaudeProvider

__all__ = [
    "ArticleSummarizer", 
    "LLMProviderType",
    "LLMProvider", 
    "OllamaProvider", 
    "ClaudeProvider"
]
