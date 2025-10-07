"""
Repositories Package
==================

Data access layer for the AI Tech News Assistant.
Contains repository classes that handle database interactions
with proper error handling, query optimization, and data mapping.
"""

from .article_repository import ArticleRepository
from .embedding_repository import EmbeddingRepository

__all__ = [
    "ArticleRepository",
    "EmbeddingRepository"
]
