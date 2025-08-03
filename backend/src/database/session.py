"""
Database Session Management
==========================

Advanced session management for SQLAlchemy operations with 
transaction handling, connection pooling, and error recovery.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

from .base import SessionLocal, create_session_factory

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Advanced database session manager with automatic retry and error handling.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize database manager.
        
        Args:
            max_retries: Maximum number of retry attempts for failed operations
            retry_delay: Delay between retry attempts in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session_factory = None
    
    def _ensure_session_factory(self):
        """Ensure session factory is available."""
        if self._session_factory is None:
            self._session_factory = create_session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy database session
            
        Raises:
            SQLAlchemyError: For database-related errors
        """
        self._ensure_session_factory()
        session = self._session_factory()
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_transaction(self) -> Generator[Session, None, None]:
        """
        Context manager for explicit transaction handling.
        
        Yields:
            Session: SQLAlchemy database session in transaction mode
        """
        self._ensure_session_factory()
        session = self._session_factory()
        
        try:
            with session.begin():
                yield session
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise
        finally:
            session.close()
    
    def execute_with_retry(self, operation, *args, **kwargs) -> Any:
        """
        Execute database operation with automatic retry on failure.
        
        Args:
            operation: Callable database operation
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Any: Result of the operation
            
        Raises:
            SQLAlchemyError: After all retries have been exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                with self.get_session() as session:
                    return operation(session, *args, **kwargs)
            except (OperationalError, IntegrityError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying: {e}")
                    import time
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Database operation failed after {self.max_retries} retries: {e}")
            except Exception as e:
                # Don't retry on non-database errors
                logger.error(f"Non-retryable database error: {e}")
                raise
        
        raise last_exception
    
    def health_check(self) -> dict:
        """
        Check database connection health.
        
        Returns:
            dict: Health status information
        """
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute("SELECT 1").scalar()
                return {
                    "status": "healthy",
                    "connection_test": result == 1,
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# Global database manager instance
db_manager = DatabaseManager()


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    with db_manager.get_session() as session:
        yield session


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for getting database session outside of FastAPI.
    
    Yields:
        Session: SQLAlchemy database session
    """
    with db_manager.get_session() as session:
        yield session


@contextmanager
def get_db_transaction() -> Generator[Session, None, None]:
    """
    Context manager for database transactions.
    
    Yields:
        Session: SQLAlchemy database session in transaction mode
    """
    with db_manager.get_transaction() as session:
        yield session


def execute_with_retry(operation, *args, **kwargs) -> Any:
    """
    Execute database operation with retry logic.
    
    Args:
        operation: Database operation function
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Any: Operation result
    """
    return db_manager.execute_with_retry(operation, *args, **kwargs)


# Utility functions for common database operations
def check_database_connection() -> bool:
    """
    Quick database connection check.
    
    Returns:
        bool: True if database is accessible
    """
    try:
        health = db_manager.health_check()
        return health["status"] == "healthy"
    except Exception:
        return False


def get_database_stats() -> dict:
    """
    Get basic database statistics.
    
    Returns:
        dict: Database statistics
    """
    try:
        with get_db_session() as session:
            # Import models here to avoid circular imports
            from .models import Article, Source, Category, Embedding, User
            
            stats = {
                "total_articles": session.query(Article).count(),
                "total_sources": session.query(Source).count(),
                "total_categories": session.query(Category).count(),
                "total_embeddings": session.query(Embedding).count(),
                "total_users": session.query(User).count(),
                "articles_with_embeddings": session.query(Article).filter(
                    Article.embedding_generated == True
                ).count(),
                "articles_with_summaries": session.query(Article).filter(
                    Article.summary_generated == True
                ).count(),
            }
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}
