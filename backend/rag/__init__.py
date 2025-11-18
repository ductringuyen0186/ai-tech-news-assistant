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

# Legacy compatibility
async def search(query: str, top_k: int = 5):
            
        Returns:
            List of relevant documents
        """
        logger.info(f"RAG search requested for query: {query[:50]}...")
        return [{"content": "Relevant document coming soon", "score": 0.9}]
