"""
Database Package
===============

SQLAlchemy database configuration and setup for the AI Tech News Assistant.
Provides ORM models, database connections, and migration support.
"""

from .base import Base, get_db, init_db, close_db
from .models import Article, User, Source, Category, ArticleCategory, Embedding
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
    "ArticleCategory",
    "Embedding",
    "DatabaseManager",
    "get_session",
]
