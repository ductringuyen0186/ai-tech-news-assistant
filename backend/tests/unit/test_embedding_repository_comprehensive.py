"""
Comprehensive Unit Tests for Embedding Repository
===============================================

Tests for embedding repository data access operations.
"""

import pytest
import sqlite3
import tempfile
import os

from src.repositories.embedding_repository import EmbeddingRepository
from src.models.embedding import SimilarityResult
from src.core.exceptions import DatabaseError


class TestEmbeddingRepository:
    """Test cases for EmbeddingRepository."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance with temporary database."""
        return EmbeddingRepository(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_embedding_data(self):
        """Sample embedding data for testing."""
        return {
            "content_id": "article_123",
            "content_type": "article",
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 76,  # 384 dimensions
            "metadata": {"title": "Test Article", "source": "test.com"}
        }
    
    @pytest.fixture
    def sample_embeddings_batch(self):
        """Sample batch of embeddings for testing."""
        base_vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 76  # 384 dimensions
        return [
            {
                "content_id": f"article_{i}",
                "content_type": "article",
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_vector": [v + i * 0.01 for v in base_vector],
                "metadata": {"title": f"Article {i}", "source": "test.com"}
            }
            for i in range(5)
        ]

    def test_repository_initialization(self, temp_db_path):
        """Test repository initialization and table creation."""
        EmbeddingRepository(db_path=temp_db_path)
        
        # Verify database file exists
        assert os.path.exists(temp_db_path)
        
        # Verify tables are created
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='embeddings'
            """)
            assert cursor.fetchone() is not None

    def test_store_embedding_success(self, repository, sample_embedding_data):
        """Test storing a single embedding."""
        embedding_id = repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=sample_embedding_data["embedding_vector"],
            metadata=sample_embedding_data["metadata"]
        )
        
        assert embedding_id is not None
        assert isinstance(embedding_id, int)
        assert embedding_id > 0

    def test_store_embedding_duplicate_content(self, repository, sample_embedding_data):
        """Test storing embedding for same content (should update)."""
        # Store first embedding
        first_id = repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=sample_embedding_data["embedding_vector"],
            metadata=sample_embedding_data["metadata"]
        )
        
        # Store second embedding for same content
        modified_vector = [v + 0.1 for v in sample_embedding_data["embedding_vector"]]
        second_id = repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=modified_vector,
            metadata=sample_embedding_data["metadata"]
        )
        
        # Should return the same ID (update, not insert)
        assert first_id == second_id

    def test_store_embedding_invalid_vector(self, repository):
        """Test storing embedding with invalid vector."""
        with pytest.raises(DatabaseError, match="Invalid embedding vector"):
            repository.store_embedding(
                content_id="test_article",
                content_type="article",
                model_name="test-model",
                embedding_vector=[],  # Empty vector
                metadata={}
            )

    def test_get_embedding_success(self, repository, sample_embedding_data):
        """Test retrieving an existing embedding."""
        # Store embedding first
        embedding_id = repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=sample_embedding_data["embedding_vector"],
            metadata=sample_embedding_data["metadata"]
        )
        
        # Retrieve embedding
        result = repository.get_embedding(
            content_id=sample_embedding_data["content_id"],
            model_name=sample_embedding_data["model_name"]
        )
        
        assert result is not None
        assert result["id"] == embedding_id
        assert result["content_id"] == sample_embedding_data["content_id"]
        assert result["model_name"] == sample_embedding_data["model_name"]
        assert len(result["embedding_vector"]) == len(sample_embedding_data["embedding_vector"])

    def test_get_embedding_not_found(self, repository):
        """Test retrieving non-existent embedding."""
        result = repository.get_embedding(
            content_id="nonexistent",
            model_name="test-model"
        )
        
        assert result is None

    def test_delete_embedding_success(self, repository, sample_embedding_data):
        """Test deleting an existing embedding."""
        # Store embedding first
        repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=sample_embedding_data["embedding_vector"],
            metadata=sample_embedding_data["metadata"]
        )
        
        # Delete embedding
        success = repository.delete_embedding(
            content_id=sample_embedding_data["content_id"],
            model_name=sample_embedding_data["model_name"]
        )
        
        assert success is True
        
        # Verify embedding is deleted
        result = repository.get_embedding(
            content_id=sample_embedding_data["content_id"],
            model_name=sample_embedding_data["model_name"]
        )
        assert result is None

    def test_delete_embedding_not_found(self, repository):
        """Test deleting non-existent embedding."""
        success = repository.delete_embedding(
            content_id="nonexistent",
            model_name="test-model"
        )
        
        assert success is False

    def test_delete_embeddings_by_content_id(self, repository, sample_embedding_data):
        """Test deleting all embeddings for a content ID."""
        content_id = sample_embedding_data["content_id"]
        
        # Store embeddings with different models
        models = ["model1", "model2", "model3"]
        for model in models:
            repository.store_embedding(
                content_id=content_id,
                content_type=sample_embedding_data["content_type"],
                model_name=model,
                embedding_vector=sample_embedding_data["embedding_vector"],
                metadata=sample_embedding_data["metadata"]
            )
        
        # Delete all embeddings for content ID
        deleted_count = repository.delete_embeddings_by_content_id(content_id)
        
        assert deleted_count == 3
        
        # Verify all embeddings are deleted
        for model in models:
            result = repository.get_embedding(content_id, model)
            assert result is None

    def test_similarity_search_cosine(self, repository, sample_embeddings_batch):
        """Test cosine similarity search."""
        # Store batch of embeddings
        for embedding_data in sample_embeddings_batch:
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=embedding_data["content_type"],
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Search with query vector similar to first embedding
        query_vector = sample_embeddings_batch[0]["embedding_vector"]
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name=sample_embeddings_batch[0]["model_name"],
            similarity_metric="cosine",
            limit=3
        )
        
        assert len(results) <= 3
        assert all(isinstance(r, SimilarityResult) for r in results)
        # First result should be the most similar (same vector)
        assert results[0].content_id == sample_embeddings_batch[0]["content_id"]
        assert results[0].similarity_score >= 0.99  # Very high similarity

    def test_similarity_search_euclidean(self, repository, sample_embeddings_batch):
        """Test Euclidean distance similarity search."""
        # Store batch of embeddings
        for embedding_data in sample_embeddings_batch:
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=embedding_data["content_type"],
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Search with query vector
        query_vector = sample_embeddings_batch[0]["embedding_vector"]
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name=sample_embeddings_batch[0]["model_name"],
            similarity_metric="euclidean",
            limit=5
        )
        
        assert len(results) <= 5
        assert all(isinstance(r, SimilarityResult) for r in results)
        # Results should be ordered by similarity (lowest distance = highest similarity)
        assert results[0].content_id == sample_embeddings_batch[0]["content_id"]

    def test_similarity_search_with_filters(self, repository, sample_embeddings_batch):
        """Test similarity search with content type filter."""
        # Store embeddings with different content types
        for i, embedding_data in enumerate(sample_embeddings_batch):
            content_type = "article" if i < 3 else "summary"
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=content_type,
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Search with content type filter
        query_vector = sample_embeddings_batch[0]["embedding_vector"]
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name=sample_embeddings_batch[0]["model_name"],
            similarity_metric="cosine",
            content_type="article",
            limit=10
        )
        
        # Should only return articles
        assert len(results) == 3
        assert all(r.content_type == "article" for r in results)

    def test_similarity_search_with_threshold(self, repository, sample_embeddings_batch):
        """Test similarity search with minimum threshold."""
        # Store embeddings
        for embedding_data in sample_embeddings_batch:
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=embedding_data["content_type"],
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Search with high threshold
        query_vector = sample_embeddings_batch[0]["embedding_vector"]
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name=sample_embeddings_batch[0]["model_name"],
            similarity_metric="cosine",
            min_similarity=0.98,  # Very high threshold
            limit=10
        )
        
        # Should return fewer results due to threshold
        assert len(results) <= len(sample_embeddings_batch)
        assert all(r.similarity_score >= 0.98 for r in results)

    def test_similarity_search_empty_database(self, repository):
        """Test similarity search with empty database."""
        query_vector = [0.1] * 384
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name="test-model",
            similarity_metric="cosine",
            limit=5
        )
        
        assert results == []

    def test_similarity_search_invalid_metric(self, repository, sample_embedding_data):
        """Test similarity search with invalid metric."""
        # Store one embedding
        repository.store_embedding(
            content_id=sample_embedding_data["content_id"],
            content_type=sample_embedding_data["content_type"],
            model_name=sample_embedding_data["model_name"],
            embedding_vector=sample_embedding_data["embedding_vector"],
            metadata=sample_embedding_data["metadata"]
        )
        
        with pytest.raises(ValueError, match="Unsupported similarity metric"):
            repository.similarity_search(
                query_vector=sample_embedding_data["embedding_vector"],
                model_name=sample_embedding_data["model_name"],
                similarity_metric="invalid_metric",
                limit=5
            )

    def test_batch_store_embeddings(self, repository, sample_embeddings_batch):
        """Test storing multiple embeddings in batch."""
        stored_ids = repository.batch_store_embeddings(sample_embeddings_batch)
        
        assert len(stored_ids) == len(sample_embeddings_batch)
        assert all(isinstance(id_, int) for id_ in stored_ids)
        
        # Verify all embeddings are stored
        for i, embedding_data in enumerate(sample_embeddings_batch):
            result = repository.get_embedding(
                content_id=embedding_data["content_id"],
                model_name=embedding_data["model_name"]
            )
            assert result is not None
            assert result["id"] == stored_ids[i]

    def test_batch_store_embeddings_partial_failure(self, repository, sample_embeddings_batch):
        """Test batch storing with some invalid embeddings."""
        # Add invalid embedding to batch
        invalid_embedding = sample_embeddings_batch[0].copy()
        invalid_embedding["embedding_vector"] = []  # Invalid empty vector
        batch_with_invalid = sample_embeddings_batch + [invalid_embedding]
        
        # Should handle partial failures gracefully
        stored_ids = repository.batch_store_embeddings(batch_with_invalid)
        
        # Should store valid embeddings and skip invalid ones
        assert len(stored_ids) == len(sample_embeddings_batch)  # Excludes invalid one

    def test_get_embeddings_by_content_type(self, repository, sample_embeddings_batch):
        """Test retrieving embeddings by content type."""
        # Store embeddings with different content types
        for i, embedding_data in enumerate(sample_embeddings_batch):
            content_type = "article" if i < 3 else "summary"
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=content_type,
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Get articles only
        articles = repository.get_embeddings_by_content_type(
            content_type="article",
            model_name=sample_embeddings_batch[0]["model_name"]
        )
        
        assert len(articles) == 3
        assert all(emb["content_type"] == "article" for emb in articles)

    def test_get_embeddings_by_model(self, repository, sample_embedding_data):
        """Test retrieving embeddings by model name."""
        models = ["model1", "model2", "model3"]
        
        # Store embeddings with different models
        for model in models:
            repository.store_embedding(
                content_id=f"content_{model}",
                content_type=sample_embedding_data["content_type"],
                model_name=model,
                embedding_vector=sample_embedding_data["embedding_vector"],
                metadata=sample_embedding_data["metadata"]
            )
        
        # Get embeddings for specific model
        model1_embeddings = repository.get_embeddings_by_model("model1")
        
        assert len(model1_embeddings) == 1
        assert model1_embeddings[0]["model_name"] == "model1"

    def test_get_embedding_stats(self, repository, sample_embeddings_batch):
        """Test getting embedding statistics."""
        # Store embeddings
        for embedding_data in sample_embeddings_batch:
            repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=embedding_data["content_type"],
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        stats = repository.get_embedding_stats()
        
        assert isinstance(stats, dict)
        assert "total_embeddings" in stats
        assert "models" in stats
        assert "content_types" in stats
        assert stats["total_embeddings"] == len(sample_embeddings_batch)

    def test_vector_normalization(self, repository):
        """Test that vectors are properly normalized."""
        # Test vector normalization utility
        vector = [3.0, 4.0, 0.0]  # Length = 5
        normalized = repository._normalize_vector(vector)
        
        # Check normalization
        assert abs(sum(x**2 for x in normalized) - 1.0) < 1e-6
        assert abs(normalized[0] - 0.6) < 1e-6  # 3/5
        assert abs(normalized[1] - 0.8) < 1e-6  # 4/5

    def test_cosine_similarity_calculation(self, repository):
        """Test cosine similarity calculation."""
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]
        vector3 = [1.0, 0.0, 0.0]
        
        # Perpendicular vectors should have similarity ~0
        sim1 = repository._calculate_cosine_similarity(vector1, vector2)
        assert abs(sim1) < 1e-6
        
        # Identical vectors should have similarity 1
        sim2 = repository._calculate_cosine_similarity(vector1, vector3)
        assert abs(sim2 - 1.0) < 1e-6

    def test_euclidean_distance_calculation(self, repository):
        """Test Euclidean distance calculation."""
        vector1 = [0.0, 0.0, 0.0]
        vector2 = [3.0, 4.0, 0.0]
        
        distance = repository._calculate_euclidean_distance(vector1, vector2)
        assert abs(distance - 5.0) < 1e-6  # 3-4-5 triangle

    def test_database_connection_error(self, repository):
        """Test handling of database connection errors."""
        # Corrupt the database path
        repository.db_path = "/invalid/path/db.sqlite"
        
        with pytest.raises(DatabaseError):
            repository.store_embedding(
                content_id="test",
                content_type="article",
                model_name="test-model",
                embedding_vector=[0.1] * 384,
                metadata={}
            )

    def test_concurrent_operations(self, repository, sample_embeddings_batch):
        """Test concurrent database operations."""
        import concurrent.futures
        
        def store_embedding(embedding_data):
            return repository.store_embedding(
                content_id=embedding_data["content_id"],
                content_type=embedding_data["content_type"],
                model_name=embedding_data["model_name"],
                embedding_vector=embedding_data["embedding_vector"],
                metadata=embedding_data["metadata"]
            )
        
        # Store embeddings concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(store_embedding, emb) for emb in sample_embeddings_batch]
            results = [future.result() for future in futures]
        
        # All operations should succeed
        assert len(results) == len(sample_embeddings_batch)
        assert all(isinstance(r, int) for r in results)

    def test_large_batch_operations(self, repository):
        """Test operations with large batches."""
        # Create large batch of embeddings
        large_batch = []
        for i in range(100):
            large_batch.append({
                "content_id": f"article_{i}",
                "content_type": "article",
                "model_name": "test-model",
                "embedding_vector": [0.1 + i * 0.001] * 384,
                "metadata": {"index": i}
            })
        
        # Store large batch
        stored_ids = repository.batch_store_embeddings(large_batch)
        
        assert len(stored_ids) == 100
        
        # Test similarity search on large dataset
        query_vector = [0.1] * 384
        results = repository.similarity_search(
            query_vector=query_vector,
            model_name="test-model",
            similarity_metric="cosine",
            limit=10
        )
        
        assert len(results) == 10
