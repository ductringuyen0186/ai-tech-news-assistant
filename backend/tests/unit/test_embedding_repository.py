"""
Unit Tests for Embedding Repository
===================================

Tests for embedding repository data access operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.repositories.embedding_repository import EmbeddingRepository
from src.core.exceptions import DatabaseError, NotFoundError, ValidationError


# Mock EmbeddingCreate and EmbeddingUpdate for tests
class EmbeddingCreate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class EmbeddingUpdate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class EmbeddingSearchRequest:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestEmbeddingRepository:
    """Test cases for EmbeddingRepository."""
    
    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance with temporary database."""
        return EmbeddingRepository(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_embedding_create_data(self):
        """Sample embedding create data for testing."""
        return {
            "text": "This is a test article about technology and AI developments.",
            "model_name": "test-model",
            "metadata": {"source": "test", "category": "technology"}
        }
    
    @pytest.fixture
    def sample_embedding_data(self):
        """Sample embedding data for testing."""
        return {
            "content_id": "test-article-1",
            "content_type": "article",
            "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 77,  # 385 dimensions
            "model_name": "test-model",
            "metadata": {"source": "test", "category": "technology"},
            "article_id": "test-article-1",
            "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 77,
            "text": "This is a test article about technology and AI developments."
        }
    
    @pytest.mark.asyncio
    async def test_create_embedding(self, repository, sample_embedding_create_data):
        """Test creating a new embedding."""
        embedding_data = EmbeddingCreate(**sample_embedding_create_data)
        
        result = await repository.create(embedding_data)
        
        assert result.id is not None
        assert result.text == sample_embedding_create_data["text"]
        assert result.model_name == sample_embedding_create_data["model_name"]
        assert result.metadata == sample_embedding_create_data["metadata"]
        assert result.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_article_id_fails(self, repository, sample_embedding_data):
        """Test that creating embedding with duplicate article_id fails."""
        embedding_data = EmbeddingCreate(**sample_embedding_data)
        
        # Create first embedding
        await repository.create(embedding_data)
        
        # Attempt to create duplicate should fail
        with pytest.raises(DatabaseError, match="already exists"):
            await repository.create(embedding_data)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, sample_embedding_data):
        """Test retrieving embedding by ID."""
        embedding_data = EmbeddingCreate(**sample_embedding_data)
        created = await repository.create(embedding_data)
        
        result = await repository.get_by_id(created.id)
        
        assert result.id == created.id
        assert result.article_id == sample_embedding_data["article_id"]
        assert result.vector == sample_embedding_data["vector"]
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test retrieving non-existent embedding raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await repository.get_by_id(999)
    
    @pytest.mark.asyncio
    async def test_get_by_article_id(self, repository, sample_embedding_data):
        """Test retrieving embedding by article ID."""
        embedding_data = EmbeddingCreate(**sample_embedding_data)
        created = await repository.create(embedding_data)
        
        result = await repository.get_by_article_id(sample_embedding_data["article_id"])
        
        assert result is not None
        assert result.id == created.id
        assert result.article_id == sample_embedding_data["article_id"]
    
    @pytest.mark.asyncio
    async def test_get_by_article_id_not_found(self, repository):
        """Test retrieving non-existent article ID returns None."""
        result = await repository.get_by_article_id("non-existent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_embedding(self, repository, sample_embedding_data):
        """Test updating an existing embedding."""
        embedding_data = EmbeddingCreate(**sample_embedding_data)
        created = await repository.create(embedding_data)
        
        new_vector = [0.9, 0.8, 0.7, 0.6, 0.5] * 100  # 500-dimensional
        update_data = EmbeddingUpdate(
            vector=new_vector,
            model_name="updated-model",
            metadata={"updated": True}
        )
        
        result = await repository.update(created.id, update_data)
        
        assert result.id == created.id
        assert result.vector == new_vector
        assert result.model_name == "updated-model"
        assert result.metadata == {"updated": True}
        assert result.article_id == sample_embedding_data["article_id"]  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_embedding(self, repository):
        """Test updating non-existent embedding raises NotFoundError."""
        update_data = EmbeddingUpdate(model_name="updated-model")
        
        with pytest.raises(NotFoundError):
            await repository.update(999, update_data)
    
    @pytest.mark.asyncio
    async def test_delete_embedding(self, repository, sample_embedding_data):
        """Test deleting an embedding."""
        embedding_data = EmbeddingCreate(**sample_embedding_data)
        created = await repository.create(embedding_data)
        
        result = await repository.delete(created.id)
        
        assert result is True
        
        # Embedding should not be found after deletion
        with pytest.raises(NotFoundError):
            await repository.get_by_id(created.id)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_embedding(self, repository):
        """Test deleting non-existent embedding raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await repository.delete(999)
    
    @pytest.mark.asyncio
    async def test_list_embeddings_no_filter(self, repository, sample_embedding_data):
        """Test listing embeddings without filters."""
        # Create multiple embeddings
        for i in range(3):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"article-{i}"}
            )
            await repository.create(embedding_data)
        
        embeddings, total_count = await repository.list_embeddings(limit=10, offset=0)
        
        assert len(embeddings) == 3
        assert total_count == 3
        assert all(embedding.id is not None for embedding in embeddings)
    
    @pytest.mark.asyncio
    async def test_list_embeddings_with_pagination(self, repository, sample_embedding_data):
        """Test listing embeddings with pagination."""
        # Create 5 embeddings
        for i in range(5):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"article-{i}"}
            )
            await repository.create(embedding_data)
        
        # Get first page
        embeddings, total_count = await repository.list_embeddings(limit=2, offset=0)
        assert len(embeddings) == 2
        assert total_count == 5
        
        # Get second page
        embeddings, total_count = await repository.list_embeddings(limit=2, offset=2)
        assert len(embeddings) == 2
        assert total_count == 5
    
    @pytest.mark.asyncio
    async def test_list_embeddings_with_content_type_filter(self, repository, sample_embedding_data):
        """Test listing embeddings filtered by content type."""
        # Create embeddings with different content types
        content_types = ["article", "summary", "article"]
        for i, content_type in enumerate(content_types):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"article-{i}", "content_type": content_type}
            )
            await repository.create(embedding_data)
        
        embeddings, total_count = await repository.list_embeddings(content_type="article")
        
        assert len(embeddings) == 2
        assert total_count == 2
        assert all(embedding.content_type == "article" for embedding in embeddings)
    
    @pytest.mark.asyncio
    async def test_list_embeddings_with_model_filter(self, repository, sample_embedding_data):
        """Test listing embeddings filtered by model name."""
        # Create embeddings with different models
        models = ["model-1", "model-2", "model-1"]
        for i, model in enumerate(models):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"article-{i}", "model_name": model}
            )
            await repository.create(embedding_data)
        
        embeddings, total_count = await repository.list_embeddings(model_name="model-1")
        
        assert len(embeddings) == 2
        assert total_count == 2
        assert all(embedding.model_name == "model-1" for embedding in embeddings)
    
    @pytest.mark.asyncio
    async def test_search_similar_embeddings(self, repository, sample_embedding_data):
        """Test similarity search functionality."""
        # Create embeddings with different vectors
        vectors = [
            [1.0, 0.0] + [0.0] * 498,  # Vector similar to query
            [0.0, 1.0] + [0.0] * 498,  # Vector dissimilar to query
            [0.9, 0.1] + [0.0] * 498   # Vector somewhat similar to query
        ]
        
        for i, vector in enumerate(vectors):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"article-{i}", "vector": vector}
            )
            await repository.create(embedding_data)
        
        # Search with query vector similar to first embedding
        query_vector = [1.0, 0.0] + [0.0] * 498
        results = await repository.search_similar(query_vector, limit=2, threshold=0.5)
        
        assert len(results) >= 1  # Should find at least the most similar one
        # Results should be ordered by similarity (highest first)
        if len(results) > 1:
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]
    
    @pytest.mark.asyncio
    async def test_search_similar_with_content_type_filter(self, repository, sample_embedding_data):
        """Test similarity search with content type filter."""
        # Create embeddings with different content types
        query_vector = [1.0, 0.0] + [0.0] * 498
        
        for i in range(3):
            content_type = "article" if i < 2 else "summary"
            embedding_data = EmbeddingCreate(
                **{
                    **sample_embedding_data, 
                    "article_id": f"article-{i}", 
                    "vector": query_vector,  # All same vector for simplicity
                    "content_type": content_type
                }
            )
            await repository.create(embedding_data)
        
        # Search only for articles
        results = await repository.search_similar(
            query_vector, 
            limit=10, 
            content_type="article"
        )
        
        assert len(results) == 2
        assert all(result["content_type"] == "article" for result in results)
    
    @pytest.mark.asyncio
    async def test_get_embeddings_by_article_ids(self, repository, sample_embedding_data):
        """Test retrieving multiple embeddings by article IDs."""
        article_ids = ["article-1", "article-2", "article-3"]
        
        # Create embeddings
        for article_id in article_ids:
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": article_id}
            )
            await repository.create(embedding_data)
        
        # Retrieve subset
        target_ids = ["article-1", "article-3"]
        results = await repository.get_embeddings_by_article_ids(target_ids)
        
        assert len(results) == 2
        retrieved_ids = [emb.article_id for emb in results]
        assert "article-1" in retrieved_ids
        assert "article-3" in retrieved_ids
        assert "article-2" not in retrieved_ids
    
    @pytest.mark.asyncio
    async def test_get_embeddings_by_article_ids_empty_list(self, repository):
        """Test retrieving embeddings with empty article IDs list."""
        results = await repository.get_embeddings_by_article_ids([])
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_embeddings_by_article_ids_nonexistent(self, repository):
        """Test retrieving embeddings with non-existent article IDs."""
        results = await repository.get_embeddings_by_article_ids(["non-existent-1", "non-existent-2"])
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_batch_create_embeddings(self, repository, sample_embedding_data):
        """Test creating multiple embeddings in batch."""
        embeddings_data = []
        for i in range(3):
            data = {**sample_embedding_data, "article_id": f"batch-article-{i}"}
            embeddings_data.append(EmbeddingCreate(**data))
        
        results = await repository.batch_create(embeddings_data)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.article_id == f"batch-article-{i}"
            assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_batch_create_with_duplicate_fails(self, repository, sample_embedding_data):
        """Test batch create with duplicate article_id fails."""
        # Create one embedding first
        first_data = EmbeddingCreate(**sample_embedding_data)
        await repository.create(first_data)
        
        # Try to batch create including the same article_id
        embeddings_data = [
            EmbeddingCreate(**{**sample_embedding_data, "article_id": "new-article"}),
            EmbeddingCreate(**sample_embedding_data)  # Duplicate
        ]
        
        with pytest.raises(DatabaseError):
            await repository.batch_create(embeddings_data)
    
    @pytest.mark.asyncio
    async def test_batch_delete_embeddings(self, repository, sample_embedding_data):
        """Test deleting multiple embeddings in batch."""
        # Create embeddings
        created_ids = []
        for i in range(3):
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, "article_id": f"delete-article-{i}"}
            )
            result = await repository.create(embedding_data)
            created_ids.append(result.id)
        
        # Batch delete
        deleted_count = await repository.batch_delete(created_ids[:2])  # Delete first 2
        
        assert deleted_count == 2
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            await repository.get_by_id(created_ids[0])
        with pytest.raises(NotFoundError):
            await repository.get_by_id(created_ids[1])
        
        # Third should still exist
        result = await repository.get_by_id(created_ids[2])
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_stats(self, repository, sample_embedding_data):
        """Test retrieving embedding statistics."""
        # Create embeddings with different models and content types
        test_data = [
            {"article_id": "article-1", "model_name": "model-a", "content_type": "article"},
            {"article_id": "article-2", "model_name": "model-a", "content_type": "summary"},
            {"article_id": "article-3", "model_name": "model-b", "content_type": "article"},
        ]
        
        for data in test_data:
            embedding_data = EmbeddingCreate(
                **{**sample_embedding_data, **data}
            )
            await repository.create(embedding_data)
        
        stats = await repository.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_embeddings" in stats
        assert "embeddings_by_model" in stats
        assert "embeddings_by_content_type" in stats
        assert "average_embedding_dim" in stats
        
        assert stats["total_embeddings"] == 3
        assert stats["embeddings_by_model"]["model-a"] == 2
        assert stats["embeddings_by_model"]["model-b"] == 1
        assert stats["embeddings_by_content_type"]["article"] == 2
        assert stats["embeddings_by_content_type"]["summary"] == 1
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_cosine(self, repository):
        """Test cosine similarity calculation."""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]  # Same vector - similarity should be 1.0
        vector3 = [0.0, 1.0, 0.0]  # Orthogonal vector - similarity should be 0.0
        
        similarity_same = repository._calculate_similarity(vector1, vector2)
        similarity_orthogonal = repository._calculate_similarity(vector1, vector3)
        
        assert abs(similarity_same - 1.0) < 0.001
        assert abs(similarity_orthogonal - 0.0) < 0.001
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_edge_cases(self, repository):
        """Test similarity calculation edge cases."""
        # Zero vectors
        zero_vector = [0.0, 0.0, 0.0]
        normal_vector = [1.0, 0.0, 0.0]
        
        # Should handle zero vectors gracefully
        similarity = repository._calculate_similarity(zero_vector, normal_vector)
        assert similarity == 0.0
        
        # Very small vectors
        small_vector1 = [1e-10, 1e-10, 1e-10]
        small_vector2 = [1e-10, 1e-10, 1e-10]
        
        similarity = repository._calculate_similarity(small_vector1, small_vector2)
        assert abs(similarity - 1.0) < 0.001


class TestEmbeddingRepositoryErrorHandling:
    """Test error handling in EmbeddingRepository."""
    
    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance with temporary database."""
        return EmbeddingRepository(db_path=temp_db_path)
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # Try to create repository with invalid path
        with pytest.raises(DatabaseError):
            repo = EmbeddingRepository(db_path="/invalid/path/database.db")
            await repo.create(EmbeddingCreate(
                article_id="test",
                content_type="article",
                vector=[0.1, 0.2],
                model_name="test",
                embedding_dim=2
            ))
    
    @pytest.mark.asyncio
    async def test_invalid_vector_dimension(self, repository):
        """Test handling of invalid vector dimensions."""
        # Vector dimension doesn't match declared dimension
        embedding_data = EmbeddingCreate(
            article_id="test-article",
            content_type="article",
            vector=[0.1, 0.2, 0.3],  # 3 dimensions
            model_name="test-model",
            embedding_dim=5  # But claiming 5 dimensions
        )
        
        # Should handle gracefully or raise appropriate error
        with pytest.raises(ValidationError):
            await repository.create(embedding_data)
    
    @pytest.mark.asyncio
    async def test_malformed_metadata(self, repository):
        """Test handling of malformed metadata."""
        # Metadata that can't be JSON serialized
        embedding_data = EmbeddingCreate(
            article_id="test-article",
            content_type="article",
            vector=[0.1, 0.2, 0.3],
            model_name="test-model",
            embedding_dim=3,
            metadata={"function": lambda x: x}
        )
        
        with pytest.raises((DatabaseError, ValidationError)):
            await repository.create(embedding_data)
