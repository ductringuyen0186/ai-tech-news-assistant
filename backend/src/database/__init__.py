"""
Database Package
===============

SQLAlchemy database configuration and setup for the AI Tech News Assistant.
Provides ORM models, database connections, and migration support.
"""

from .base import Base, get_db, init_db, close_db
from .models import Article, User, Source, Category, article_category_association, Embedding
from .session import DatabaseManager, get_session

__all__ = [
    "Base",
    "get_db", 
    "init_db",
    "close_db",
    "Article",
    "User", 
    "Source",
    "Category",
    "article_category_association",
    "Embedding",
    "DatabaseManager",
    "get_session",
]
