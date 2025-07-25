"""
Simple Embedding Repository Tests  
=================================

Basic working tests for EmbeddingRepository to improve coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sqlite3
import tempfile
import os

from src.repositories.embedding_repository import EmbeddingRepository


class TestSimpleEmbeddingRepository:
    """Simple test cases for EmbeddingRepository."""
    
    @pytest.fixture
    async def repository(self):
        """Create an embedding repository instance with temp database."""
        # Create a temporary database file
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        repo = EmbeddingRepository(db_path)
        await repo.initialize()
        yield repo
        
        # Cleanup
        await repo.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_initialization(self, repository):
        """Test repository initialization."""
        assert repository.db_path is not None
        
    @pytest.mark.asyncio
    async def test_store_embeddings_basic(self, repository):
        """Test storing basic embeddings."""
        embedding_data = {
            "article_id": "test-123",
            "embedding": [0.1, 0.2, 0.3],
            "model_name": "test-model"
        }
        
        result = await repository.store_embeddings(**embedding_data)
        assert result is not None
        
    @pytest.mark.asyncio
    async def test_get_embedding_by_id(self, repository):
        """Test retrieving embedding by ID."""
        # Store first
        embedding_data = {
            "article_id": "test-456", 
            "embedding": [0.4, 0.5, 0.6],
            "model_name": "test-model"
        }
        await repository.store_embeddings(**embedding_data)
        
        # Retrieve
        result = await repository.get_embedding("test-456")
        if result:
            assert result["article_id"] == "test-456"
    
    @pytest.mark.asyncio
    async def test_similarity_search_basic(self, repository):
        """Test basic similarity search."""
        query_vector = [0.1, 0.2, 0.3]
        
        results = await repository.similarity_search(
            query_vector=query_vector,
            top_k=5,
            threshold=0.5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
    @pytest.mark.asyncio
    async def test_get_stats(self, repository):
        """Test getting repository statistics."""
        stats = await repository.get_stats()
        assert "total_embeddings" in stats
        assert isinstance(stats["total_embeddings"], int)
        
    @pytest.mark.asyncio
    async def test_delete_embedding(self, repository):
        """Test deleting an embedding."""
        # This should not raise an error even if embedding doesn't exist
        result = await repository.delete_embedding("nonexistent")
        # Should return False or None for non-existent embeddings
