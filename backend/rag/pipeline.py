"""
RAG Pipeline Implementation
===========================

Complete Retrieval-Augmented Generation pipeline combining:
1. Semantic search (retrieval)
2. Context augmentation
3. LLM generation (Groq)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RAGPipeline:
    """
    Complete RAG pipeline for intelligent article retrieval and summarization.
    
    Features:
    - Semantic search using embeddings
    - Context ranking and filtering
    - LLM-powered answer generation
    - Source attribution
    """
    
    def __init__(self):
        """Initialize RAG pipeline with search and LLM services."""
        self.search_service = None
        self.llm_provider = None
        self._initialized = False
        logger.info("RAG Pipeline created - awaiting initialization")
    
    async def initialize(self):
        """Initialize search service and LLM provider."""
        if self._initialized:
            return
        
        try:
            # Import here to avoid circular dependencies
            from src.services.search_service import SearchService
            from llm.factory import get_llm_provider
            
            # Initialize search service
            self.search_service = SearchService()
            await self.search_service.initialize()
            
            # Initialize LLM provider (Groq preferred)
            self.llm_provider = await get_llm_provider()
            
            self._initialized = True
            logger.info("RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Pipeline: {e}")
            raise
    
    async def query(
        self,
        question: str,
        top_k: int = 5,
        min_score: float = 0.7,
        use_reranking: bool = True,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User's question
            top_k: Number of articles to retrieve
            min_score: Minimum similarity score
            use_reranking: Whether to rerank results
            include_sources: Include source articles in response
            
        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            await self.initialize()
            
            # Step 1: Retrieve relevant articles (semantic search)
            search_request = self._build_search_request(
                query=question,
                top_k=top_k,
                min_score=min_score,
                use_reranking=use_reranking
            )
            
            search_results = await self.search_service.search(search_request)
            
            if not search_results.results:
                return {
                    "answer": "I couldn't find any relevant articles to answer your question.",
                    "sources": [],
                    "confidence": 0.0,
                    "metadata": {
                        "articles_found": 0,
                        "search_time_ms": search_results.execution_time_ms
                    }
                }
            
            # Step 2: Build context from retrieved articles
            context = self._build_context(search_results.results)
            
            # Step 3: Generate answer using LLM (Groq)
            answer = await self._generate_answer(question, context)
            
            # Step 4: Format response
            response = {
                "answer": answer["text"],
                "sources": self._format_sources(search_results.results) if include_sources else [],
                "confidence": self._calculate_confidence(search_results.results),
                "metadata": {
                    "articles_found": len(search_results.results),
                    "search_time_ms": search_results.execution_time_ms,
                    "llm_model": answer.get("model"),
                    "llm_provider": answer.get("provider"),
                    "tokens_used": answer.get("tokens_used"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    async def summarize_with_context(
        self,
        text: str,
        context_query: Optional[str] = None,
        max_context_articles: int = 3
    ) -> Dict[str, Any]:
        """
        Summarize text with additional context from related articles.
        
        Args:
            text: Text to summarize
            context_query: Optional query to find related articles
            max_context_articles: Maximum context articles to include
            
        Returns:
            Summary with context and sources
        """
        try:
            await self.initialize()
            
            # Get related articles if context query provided
            context_articles = []
            if context_query:
                search_request = self._build_search_request(
                    query=context_query,
                    top_k=max_context_articles,
                    min_score=0.6
                )
                search_results = await self.search_service.search(search_request)
                context_articles = search_results.results
            
            # Build augmented context
            context = f"Text to summarize:\n{text}\n\n"
            if context_articles:
                context += "Related context:\n"
                for i, article in enumerate(context_articles, 1):
                    context += f"{i}. {article.title}: {article.summary or article.content[:200]}\n"
            
            # Generate summary using LLM
            prompt = f"""Based on the following text and related context, provide a comprehensive summary.
Focus on key points, technical details, and implications.

{context}

Summary:"""
            
            summary = await self.llm_provider.summarize(prompt)
            
            return {
                "summary": summary.get("summary", ""),
                "context_articles": self._format_sources(context_articles),
                "metadata": {
                    "context_articles_count": len(context_articles),
                    "model": summary.get("model"),
                    "provider": summary.get("provider")
                }
            }
            
        except Exception as e:
            logger.error(f"Context summarization failed: {e}")
            return {
                "summary": f"Summarization failed: {str(e)}",
                "context_articles": [],
                "metadata": {"error": str(e)}
            }
    
    def _build_search_request(self, query: str, top_k: int, min_score: float, use_reranking: bool = True):
        """Build search request object."""
        from src.models.search import SearchRequest
        
        return SearchRequest(
            query=query,
            limit=top_k,
            min_score=min_score,
            use_reranking=use_reranking,
            include_summary=True,
            sources=None,
            categories=None,
            date_from=None,
            date_to=None
        )
    
    def _build_context(self, articles: List[Any]) -> str:
        """Build context string from retrieved articles."""
        context = "Relevant articles:\n\n"
        
        for i, article in enumerate(articles, 1):
            context += f"Article {i}:\n"
            context += f"Title: {article.title}\n"
            context += f"Source: {article.source}\n"
            
            # Use summary if available, otherwise use content preview
            content = article.summary or article.content
            if content:
                context += f"Content: {content[:500]}...\n"
            
            context += f"Relevance Score: {article.similarity_score:.2f}\n\n"
        
        return context
    
    async def _generate_answer(self, question: str, context: str) -> Dict[str, Any]:
        """Generate answer using LLM with context."""
        prompt = f"""You are a knowledgeable AI assistant specializing in technology news and developments.
Based on the following articles, answer the user's question accurately and concisely.

{context}

Question: {question}

Instructions:
- Provide a clear, informative answer based on the articles
- Include specific details and technical information when relevant
- If the articles don't fully answer the question, acknowledge the limitations
- Keep the answer concise but comprehensive (2-4 paragraphs)

Answer:"""
        
        try:
            result = await self.llm_provider.summarize(prompt)
            
            return {
                "text": result.get("summary", ""),
                "model": result.get("model"),
                "provider": result.get("provider"),
                "tokens_used": result.get("tokens_used"),
                "success": result.get("success", False)
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "text": "I apologize, but I couldn't generate a response at this time.",
                "error": str(e),
                "success": False
            }
    
    def _format_sources(self, articles: List[Any]) -> List[Dict[str, Any]]:
        """Format articles as source references."""
        sources = []
        
        for article in articles:
            source = {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at,
                "similarity_score": article.similarity_score,
                "relevance_score": article.relevance_score
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, articles: List[Any]) -> float:
        """Calculate confidence score based on search results."""
        if not articles:
            return 0.0
        
        # Average of top 3 similarity scores
        top_scores = [article.similarity_score for article in articles[:3]]
        confidence = sum(top_scores) / len(top_scores)
        
        # Adjust based on number of articles
        if len(articles) < 3:
            confidence *= 0.8
        
        return round(confidence, 2)


# Singleton instance
_rag_pipeline = None


async def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline singleton."""
    global _rag_pipeline
    
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
        await _rag_pipeline.initialize()
    
    return _rag_pipeline
