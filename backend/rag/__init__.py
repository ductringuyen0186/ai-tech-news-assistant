"""
RAG (Retrieval-Augmented Generation) Module
===========================================

Complete RAG pipeline implementation combining:
- Semantic search for document retrieval
- Context augmentation from relevant articles
- LLM-powered answer generation using Groq

Features:
- Question answering with source attribution
- Context-aware summarization
- Configurable retrieval parameters
- Multiple LLM provider support
"""

from .pipeline import RAGPipeline, get_rag_pipeline

__all__ = ["RAGPipeline", "get_rag_pipeline"]
