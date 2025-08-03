"""
Repository Factory
=================

Factory pattern for creating repository instances.
Supports both legacy SQLite repositories and new SQLAlchemy ORM repositories.
"""

import logging
from typing import Protocol, runtime_checkable
from enum import Enum

from ..core.config import get_settings
from ..repositories.article_repository_final import ArticleRepository as SQLiteArticleRepository
from ..repositories.sqlalchemy_repository import SQLAlchemyArticleRepository

logger = logging.getLogger(__name__)


class RepositoryType(Enum):
    """Repository implementation types."""
    SQLITE = "sqlite"
    SQLALCHEMY = "sqlalchemy"


@runtime_checkable
class ArticleRepositoryProtocol(Protocol):
    """Protocol defining the article repository interface."""
    
    async def create(self, article):
        """Create a new article."""
        ...
    
    async def get_by_id(self, article_id: int):
        """Get article by ID."""
        ...
    
    async def get_by_url(self, url: str):
        """Get article by URL."""
        ...
    
    async def update(self, article_id: int, update_data):
        """Update an article."""
        ...
    
    async def delete(self, article_id: int):
        """Delete an article."""
        ...
    
    async def list_articles(self, limit: int = 50, offset: int = 0, source: str = None):
        """List articles with pagination."""
        ...
    
    async def search_articles(self, query: str, limit: int = 50, offset: int = 0):
        """Search articles."""
        ...
    
    async def get_articles_without_embeddings(self, limit: int = 100):
        """Get articles without embeddings."""
        ...
    
    async def mark_embedding_generated(self, article_id: int):
        """Mark article as having embeddings generated."""
        ...
    
    async def get_stats(self):
        """Get repository statistics."""
        ...


class RepositoryFactory:
    """
    Factory for creating repository instances.
    
    Automatically selects the appropriate repository implementation
    based on configuration and feature flags.
    """
    
    def __init__(self):
        """Initialize the factory."""
        self._article_repository = None
        self._repository_type = None
        self._determine_repository_type()
    
    def _determine_repository_type(self):
        """Determine which repository type to use."""
        settings = get_settings()
        
        # Use environment variable or feature flag to determine repository type
        use_sqlalchemy = getattr(settings, 'use_sqlalchemy_orm', True)
        
        # For now, default to SQLAlchemy for new Issue #28 implementation
        if use_sqlalchemy:
            self._repository_type = RepositoryType.SQLALCHEMY
            logger.info("Using SQLAlchemy ORM repository")
        else:
            self._repository_type = RepositoryType.SQLITE
            logger.info("Using legacy SQLite repository")
    
    def get_article_repository(self) -> ArticleRepositoryProtocol:
        """
        Get article repository instance.
        
        Returns:
            ArticleRepositoryProtocol: Article repository implementation
        """
        if self._article_repository is None:
            self._article_repository = self._create_article_repository()
        
        return self._article_repository
    
    def _create_article_repository(self) -> ArticleRepositoryProtocol:
        """Create the appropriate article repository instance."""
        if self._repository_type == RepositoryType.SQLALCHEMY:
            return SQLAlchemyArticleRepository()
        elif self._repository_type == RepositoryType.SQLITE:
            # Use the legacy SQLite repository
            settings = get_settings()
            db_path = getattr(settings, 'database_url', './data/ai_news.db')
            if db_path.startswith('sqlite:///'):
                db_path = db_path.replace('sqlite:///', '')
            return SQLiteArticleRepository(db_path)
        else:
            raise ValueError(f"Unknown repository type: {self._repository_type}")
    
    def get_repository_type(self) -> RepositoryType:
        """Get the current repository type."""
        return self._repository_type
    
    def switch_repository_type(self, repo_type: RepositoryType):
        """
        Switch to a different repository type.
        
        Args:
            repo_type: The repository type to switch to
        """
        if repo_type != self._repository_type:
            logger.info(f"Switching repository type from {self._repository_type} to {repo_type}")
            self._repository_type = repo_type
            self._article_repository = None  # Reset to force recreation
    
    def get_repository_info(self) -> dict:
        """
        Get information about the current repository configuration.
        
        Returns:
            dict: Repository information
        """
        return {
            "type": self._repository_type.value,
            "implementation": type(self.get_article_repository()).__name__,
            "supports_transactions": self._repository_type == RepositoryType.SQLALCHEMY,
            "supports_relationships": self._repository_type == RepositoryType.SQLALCHEMY,
            "supports_migrations": self._repository_type == RepositoryType.SQLALCHEMY,
        }


# Global factory instance
_repository_factory = None


def get_repository_factory() -> RepositoryFactory:
    """
    Get the global repository factory instance.
    
    Returns:
        RepositoryFactory: The repository factory
    """
    global _repository_factory
    if _repository_factory is None:
        _repository_factory = RepositoryFactory()
    return _repository_factory


def get_article_repository() -> ArticleRepositoryProtocol:
    """
    Convenience function to get the article repository.
    
    Returns:
        ArticleRepositoryProtocol: Article repository implementation
    """
    factory = get_repository_factory()
    return factory.get_article_repository()


# Dependency injection for FastAPI
async def get_article_repository_dependency() -> ArticleRepositoryProtocol:
    """
    FastAPI dependency for getting article repository.
    
    Returns:
        ArticleRepositoryProtocol: Article repository implementation
    """
    return get_article_repository()


class RepositoryMigrator:
    """
    Helper class for migrating between repository implementations.
    """
    
    def __init__(self, factory: RepositoryFactory):
        """
        Initialize migrator.
        
        Args:
            factory: Repository factory instance
        """
        self.factory = factory
    
    async def migrate_to_sqlalchemy(self) -> bool:
        """
        Migrate from SQLite to SQLAlchemy repository.
        
        Returns:
            bool: True if migration was successful
        """
        try:
            logger.info("Starting migration to SQLAlchemy repository")
            
            # Initialize SQLAlchemy database
            from ..database.init_db import setup_database
            if not setup_database():
                logger.error("Failed to setup SQLAlchemy database")
                return False
            
            # Switch to SQLAlchemy repository
            self.factory.switch_repository_type(RepositoryType.SQLALCHEMY)
            
            # Verify the switch worked
            repo = self.factory.get_article_repository()
            if not isinstance(repo, SQLAlchemyArticleRepository):
                logger.error("Failed to switch to SQLAlchemy repository")
                return False
            
            logger.info("Successfully migrated to SQLAlchemy repository")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate to SQLAlchemy repository: {e}")
            return False
    
    async def test_repository_compatibility(self) -> dict:
        """
        Test that both repository implementations work correctly.
        
        Returns:
            dict: Test results
        """
        results = {
            "sqlite": {"available": False, "error": None},
            "sqlalchemy": {"available": False, "error": None}
        }
        
        # Test SQLite repository
        try:
            self.factory.switch_repository_type(RepositoryType.SQLITE)
            sqlite_repo = self.factory.get_article_repository()
            # Try to get stats as a simple test
            await sqlite_repo.get_stats()
            results["sqlite"]["available"] = True
        except Exception as e:
            results["sqlite"]["error"] = str(e)
        
        # Test SQLAlchemy repository
        try:
            self.factory.switch_repository_type(RepositoryType.SQLALCHEMY)
            sqlalchemy_repo = self.factory.get_article_repository()
            # Try to get stats as a simple test
            await sqlalchemy_repo.get_stats()
            results["sqlalchemy"]["available"] = True
        except Exception as e:
            results["sqlalchemy"]["error"] = str(e)
        
        return results


def create_repository_migrator() -> RepositoryMigrator:
    """
    Create a repository migrator instance.
    
    Returns:
        RepositoryMigrator: Migrator instance
    """
    factory = get_repository_factory()
    return RepositoryMigrator(factory)
