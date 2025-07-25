"""
Unit Tests for Article Repository
================================

Tests for article repository data access operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, ArticleUpdate, ArticleSearchRequest
from src.core.exceptions import DatabaseError, NotFoundError


class TestArticleRepository:
    """Test cases for ArticleRepository."""
    
    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance with temporary database."""
        return ArticleRepository(db_path=temp_db_path)
    
    @pytest.mark.asyncio
    async def test_create_article(self, repository, sample_article_data):
        """Test creating a new article."""
        article_data = ArticleCreate(**sample_article_data)
        
        result = await repository.create(article_data)
        
        assert result.id is not None
        assert result.title == sample_article_data["title"]
        assert result.url == sample_article_data["url"]
        assert result.content == sample_article_data["content"]
        assert result.author == sample_article_data["author"]
        assert result.source == sample_article_data["source"]
    
    @pytest.mark.asyncio
    async def test_create_duplicate_url_fails(self, repository, sample_article_data):
        """Test that creating article with duplicate URL fails."""
        article_data = ArticleCreate(**sample_article_data)
        
        # Create first article
        await repository.create(article_data)
        
        # Attempt to create duplicate should fail
        with pytest.raises(DatabaseError, match="already exists"):
            await repository.create(article_data)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, sample_article_data):
        """Test retrieving article by ID."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        result = await repository.get_by_id(created.id)
        
        assert result.id == created.id
        assert result.title == sample_article_data["title"]
        assert result.view_count == 1  # Should increment on view
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test retrieving non-existent article raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await repository.get_by_id(999)
    
    @pytest.mark.asyncio
    async def test_get_by_url(self, repository, sample_article_data):
        """Test retrieving article by URL."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        result = await repository.get_by_url(sample_article_data["url"])
        
        assert result is not None
        assert result.id == created.id
        assert result.url == sample_article_data["url"]
    
    @pytest.mark.asyncio
    async def test_get_by_url_not_found(self, repository):
        """Test retrieving non-existent URL returns None."""
        result = await repository.get_by_url("https://nonexistent.com")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_article(self, repository, sample_article_data):
        """Test updating an existing article."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        update_data = ArticleUpdate(
            title="Updated Title",
            summary="New summary"
        )
        
        result = await repository.update(created.id, update_data)
        
        assert result.id == created.id
        assert result.title == "Updated Title"
        assert result.summary == "New summary"
        assert result.content == sample_article_data["content"]  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_article(self, repository):
        """Test updating non-existent article raises NotFoundError."""
        update_data = ArticleUpdate(title="Updated Title")
        
        with pytest.raises(NotFoundError):
            await repository.update(999, update_data)
    
    @pytest.mark.asyncio
    async def test_delete_article(self, repository, sample_article_data):
        """Test soft deleting an article."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        result = await repository.delete(created.id)
        
        assert result is True
        
        # Article should not be found after deletion
        with pytest.raises(NotFoundError):
            await repository.get_by_id(created.id)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_article(self, repository):
        """Test deleting non-existent article raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await repository.delete(999)
    
    @pytest.mark.asyncio
    async def test_list_articles_no_filter(self, repository, sample_article_data):
        """Test listing articles without filters."""
        # Create multiple articles
        for i in range(3):
            article_data = ArticleCreate(
                **{**sample_article_data, "url": f"https://example.com/article-{i}"}
            )
            await repository.create(article_data)
        
        articles, total_count = await repository.list_articles(limit=10, offset=0)
        
        assert len(articles) == 3
        assert total_count == 3
        assert all(article.id is not None for article in articles)
    
    @pytest.mark.asyncio
    async def test_list_articles_with_pagination(self, repository, sample_article_data):
        """Test listing articles with pagination."""
        # Create 5 articles
        for i in range(5):
            article_data = ArticleCreate(
                **{**sample_article_data, "url": f"https://example.com/article-{i}"}
            )
            await repository.create(article_data)
        
        # Get first page
        articles, total_count = await repository.list_articles(limit=2, offset=0)
        assert len(articles) == 2
        assert total_count == 5
        
        # Get second page
        articles, total_count = await repository.list_articles(limit=2, offset=2)
        assert len(articles) == 2
        assert total_count == 5
    
    @pytest.mark.asyncio
    async def test_list_articles_with_source_filter(self, repository, sample_article_data):
        """Test listing articles filtered by source."""
        # Create articles with different sources
        sources = ["source1.com", "source2.com", "source1.com"]
        for i, source in enumerate(sources):
            article_data = ArticleCreate(
                **{**sample_article_data, "url": f"https://example.com/article-{i}", "source": source}
            )
            await repository.create(article_data)
        
        filter_params = ArticleSearchRequest(source="source1.com")
        articles, total_count = await repository.list_articles(source="source1.com")
        
        assert len(articles) == 2
        assert total_count == 2
        assert all(article.source == "source1.com" for article in articles)
    
    @pytest.mark.asyncio
    async def test_search_articles(self, repository, sample_article_data):
        """Test text search functionality."""
        # Create articles with different titles
        titles = ["AI Technology News", "Machine Learning Update", "Tech Industry Report"]
        for i, title in enumerate(titles):
            article_data = ArticleCreate(
                **{**sample_article_data, "url": f"https://example.com/article-{i}", "title": title}
            )
            await repository.create(article_data)
        
        results = await repository.search_articles("AI", limit=10)
        
        assert len(results) == 1
        assert "AI Technology News" in results[0].title
    
    @pytest.mark.asyncio
    async def test_get_articles_without_embeddings(self, repository, sample_article_data):
        """Test retrieving articles without embeddings."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        results = await repository.get_articles_without_embeddings()
        
        assert len(results) == 1
        assert results[0].id == created.id
        assert results[0].embedding_generated is False
    
    @pytest.mark.asyncio
    async def test_mark_embedding_generated(self, repository, sample_article_data):
        """Test marking article as having embeddings generated."""
        article_data = ArticleCreate(**sample_article_data)
        created = await repository.create(article_data)
        
        await repository.mark_embedding_generated(created.id)
        
        # Verify embedding_generated flag is updated
        articles = await repository.get_articles_without_embeddings()
        assert len(articles) == 0  # Should be empty since embedding is marked as generated
    
    @pytest.mark.asyncio
    async def test_get_stats(self, repository, sample_article_data):
        """Test retrieving article statistics."""
        # Create some test data
        article_data = ArticleCreate(**sample_article_data)
        await repository.create(article_data)
        
        stats = await repository.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_articles" in stats
        assert "articles_with_summaries" in stats
        assert "articles_with_embeddings" in stats
        assert "top_sources" in stats
        assert stats["total_articles"] >= 1
