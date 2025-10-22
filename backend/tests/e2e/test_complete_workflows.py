"""
End-to-End Tests for AI Tech News Assistant
==========================================

Complete workflow tests that verify the entire application functionality
from ingestion to search.
"""

import pytest
import asyncio
from unittest.mock import patch


class TestCompleteWorkflows:
    """Test complete application workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_news_processing_workflow(self, temp_db_path, sample_article_data):
        """
        Test complete workflow: RSS ingestion -> Article storage -> Summary generation -> Embedding generation -> Search
        """
        from src.repositories.article_repository import ArticleRepository
        from src.repositories.embedding_repository import EmbeddingRepository
        from src.services.news_service import NewsService
        from src.services.summarization_service import SummarizationService
        from src.services.embedding_service import EmbeddingService
        from src.models.article import ArticleCreate, SummarizationRequest
        
        # Initialize repositories
        article_repo = ArticleRepository(db_path=temp_db_path)
        embedding_repo = EmbeddingRepository(db_path=temp_db_path)
        
        # Step 1: RSS Ingestion (mocked)
        with patch.object(NewsService, 'fetch_rss_feeds') as mock_fetch:
            mock_fetch.return_value = [ArticleCreate(**sample_article_data)]
            
            news_service = NewsService()
            articles = await news_service.fetch_rss_feeds()
        
        assert len(articles) == 1
        
        # Step 2: Store articles
        stored_article = await article_repo.create(articles[0])
        assert stored_article.id is not None
        
        # Step 3: Generate summary (mocked)
        with patch.object(SummarizationService, 'summarize_content') as mock_summarize:
            from src.models.article import AISummary
            
            mock_summary = AISummary(
                summary="This is a test summary of the article content.",
                provider="test",
                model="test-model",
                content_length=len(sample_article_data["content"])
            )
            mock_summarize.return_value = mock_summary
            
            summarization_service = SummarizationService()
            request = SummarizationRequest(
                content=stored_article.content,
                max_length=100
            )
            summary_result = await summarization_service.summarize_content(request)
        
        assert summary_result.summary == "This is a test summary of the article content."
        
        # Update article with summary
        from src.models.article import ArticleUpdate
        update_data = ArticleUpdate(summary=summary_result.summary)
        updated_article = await article_repo.update(stored_article.id, update_data)
        assert updated_article.summary is not None
        
        # Step 4: Generate embeddings (mocked)
        with patch.object(EmbeddingService, 'generate_embeddings') as mock_embed:
            from src.models.embedding import EmbeddingResponse
            
            mock_embed_response = EmbeddingResponse(
                embeddings=[[0.1, 0.2, 0.3] * 128],  # 384-dim vector
                model_name="test-model",
                embedding_dim=384,
                processing_time=0.1
            )
            mock_embed.return_value = mock_embed_response
            
            embedding_service = EmbeddingService()
            from src.models.embedding import EmbeddingRequest
            
            embed_request = EmbeddingRequest(texts=[updated_article.content])
            embed_result = await embedding_service.generate_embeddings(embed_request)
        
        # Store embedding
        embedding_id = embedding_repo.store_embedding(
            content_id=str(updated_article.id),
            content_type="article",
            embedding_vector=embed_result.embeddings[0],
            model_name=embed_result.model_name,
            metadata={
                "title": updated_article.title,
                "source": updated_article.source,
                "content_snippet": updated_article.content[:200]
            }
        )
        assert embedding_id is not None
        
        # Mark article as having embeddings
        await article_repo.mark_embedding_generated(updated_article.id)
        
        # Step 5: Verify search functionality
        # Text search
        search_results = await article_repo.search_articles("test", limit=10)
        assert len(search_results) >= 1
        
        # Similarity search
        query_embedding = [0.1, 0.2, 0.3] * 128  # Similar to stored embedding
        similarity_results = embedding_repo.similarity_search(
            query_embedding=query_embedding,
            model_name="test-model",
            top_k=5,
            similarity_threshold=0.5
        )
        assert len(similarity_results) >= 1
        assert similarity_results[0].id == f"article:{updated_article.id}"
    
    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, temp_db_path, sample_article_data):
        """Test batch processing of multiple articles."""
        from src.repositories.article_repository import ArticleRepository
        from src.models.article import ArticleCreate
        
        repo = ArticleRepository(db_path=temp_db_path)
        
        # Create multiple articles
        articles = []
        for i in range(5):
            article_data = {
                **sample_article_data,
                "url": f"https://example.com/article-{i}",
                "title": f"Test Article {i}"
            }
            article = await repo.create(ArticleCreate(**article_data))
            articles.append(article)
        
        # Verify all articles were created
        all_articles, total_count = await repo.list_articles(limit=10)
        assert len(all_articles) == 5
        assert total_count == 5
        
        # Test getting articles without embeddings
        articles_without_embeddings = await repo.get_articles_without_embeddings()
        assert len(articles_without_embeddings) == 5
        
        # Mark some as having embeddings
        for i in range(3):
            await repo.mark_embedding_generated(articles[i].id)
        
        # Verify filtering works
        remaining_articles = await repo.get_articles_without_embeddings()
        assert len(remaining_articles) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, temp_db_path, sample_article_data):
        """Test error handling in complete workflow."""
        from src.repositories.article_repository import ArticleRepository
        from src.services.summarization_service import SummarizationService
        from src.models.article import ArticleCreate, SummarizationRequest
        from src.core.exceptions import LLMError
        
        repo = ArticleRepository(db_path=temp_db_path)
        
        # Create article
        article = await repo.create(ArticleCreate(**sample_article_data))
        
        # Test summarization failure handling
        with patch.object(SummarizationService, 'summarize_content') as mock_summarize:
            mock_summarize.side_effect = LLMError("All providers failed")
            
            service = SummarizationService()
            request = SummarizationRequest(content=article.content)
            
            with pytest.raises(LLMError):
                await service.summarize_content(request)
        
        # Verify article is still accessible despite summarization failure
        retrieved = await repo.get_by_id(article.id)
        assert retrieved.id == article.id
        assert retrieved.summary is None  # No summary due to failure
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_db_path, sample_article_data):
        """Test concurrent operations on the system."""
        from src.repositories.article_repository import ArticleRepository
        from src.models.article import ArticleCreate
        
        repo = ArticleRepository(db_path=temp_db_path)
        
        async def create_article(index):
            article_data = {
                **sample_article_data,
                "url": f"https://example.com/concurrent-{index}",
                "title": f"Concurrent Article {index}"
            }
            return await repo.create(ArticleCreate(**article_data))
        
        # Create articles concurrently
        tasks = [create_article(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        successful_creates = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_creates) == 10
        
        # Verify all articles are in database
        all_articles, total_count = await repo.list_articles(limit=20)
        assert total_count == 10
    
    @pytest.mark.asyncio
    async def test_data_consistency_workflow(self, temp_db_path, sample_article_data):
        """Test data consistency across operations."""
        from src.repositories.article_repository import ArticleRepository
        from src.repositories.embedding_repository import EmbeddingRepository
        from src.models.article import ArticleCreate, ArticleUpdate
        
        article_repo = ArticleRepository(db_path=temp_db_path)
        embedding_repo = EmbeddingRepository(db_path=temp_db_path)
        
        # Create article
        article = await article_repo.create(ArticleCreate(**sample_article_data))
        original_id = article.id
        
        # Store embedding
        embedding_vector = [0.1] * 384
        embedding_repo.store_embedding(
            content_id=str(article.id),
            content_type="article",
            embedding_vector=embedding_vector,
            model_name="test-model"
        )
        
        # Update article
        update_data = ArticleUpdate(summary="Updated summary")
        updated_article = await article_repo.update(article.id, update_data)
        
        # Verify data consistency
        assert updated_article.id == original_id
        assert updated_article.summary == "Updated summary"
        assert updated_article.title == article.title  # Unchanged fields preserved
        
        # Verify embedding still exists and is linked correctly
        retrieved_embedding = embedding_repo.get_embedding(
            content_id=str(article.id),
            content_type="article",
            model_name="test-model"
        )
        assert retrieved_embedding is not None
        
        # Delete article (soft delete)
        await article_repo.delete(article.id)
        
        # Verify article is not found in normal queries
        from src.core.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            await article_repo.get_by_id(article.id)
        
        # But embedding might still exist (depending on cleanup policy)
        # This tests referential integrity concerns
