"""
SQLAlchemy ORM Repository
========================

Repository pattern implementation using SQLAlchemy ORM models.
Provides type-safe database operations with proper relationship handling.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import IntegrityError

from ..database.models import (
    Article as ArticleModel, 
    Source as SourceModel, 
    Category as CategoryModel
)
from ..database.session import get_db_session, get_db_transaction
from ..models.article import Article, ArticleCreate, ArticleUpdate
from ..core.exceptions import DatabaseError, NotFoundError

import logging

logger = logging.getLogger(__name__)


class SQLAlchemyArticleRepository:
    """
    Article repository using SQLAlchemy ORM.
    
    Provides CRUD operations and advanced querying for articles
    with proper relationship management and performance optimization.
    """
    
    def __init__(self):
        """Initialize the repository."""
        pass
    
    def _model_to_pydantic(self, article_model: ArticleModel) -> Article:
        """
        Convert SQLAlchemy model to Pydantic model.
        
        Args:
            article_model: SQLAlchemy Article model instance
            
        Returns:
            Article: Pydantic Article model
        """
        return Article(
            id=article_model.id,
            title=article_model.title,
            url=article_model.url,
            content=article_model.content,
            summary=article_model.summary,
            source=article_model.source.name if article_model.source else "Unknown",
            author=article_model.author,
            published_at=article_model.published_at,
            categories=[cat.name for cat in article_model.categories] if article_model.categories else [],
            metadata=article_model.metadata,
            created_at=article_model.created_at,
            updated_at=article_model.updated_at,
            is_archived=article_model.is_archived,
            view_count=article_model.view_count,
            embedding_generated=article_model.embedding_generated,
            published_date=article_model.published_at,  # Compatibility
        )
    
    async def create(self, article_data: ArticleCreate) -> Article:
        """
        Create a new article.
        
        Args:
            article_data: Article creation data
            
        Returns:
            Article: Created article
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            with get_db_transaction() as session:
                # Check if article with URL already exists
                existing = session.query(ArticleModel).filter(
                    ArticleModel.url == article_data.url
                ).first()
                
                if existing:
                    raise DatabaseError(f"Article with URL already exists: {article_data.url}")
                
                # Find or create source
                source = None
                if hasattr(article_data, 'source') and article_data.source:
                    source = session.query(SourceModel).filter(
                        SourceModel.name == article_data.source
                    ).first()
                    
                    if not source:
                        source = SourceModel(
                            name=article_data.source,
                            url=article_data.url,  # Use article URL as fallback
                            is_active=True
                        )
                        session.add(source)
                        session.flush()  # Get the ID
                
                # Create article
                article_model = ArticleModel(
                    title=article_data.title,
                    url=article_data.url,
                    content=article_data.content,
                    summary=article_data.summary,
                    author=getattr(article_data, 'author', None),
                    published_at=getattr(article_data, 'published_at', None) or 
                                 getattr(article_data, 'published_date', None),
                    source_id=source.id if source else None,
                    metadata=getattr(article_data, 'metadata', None),
                    language='en',  # Default language
                    word_count=len(article_data.content.split()) if article_data.content else 0,
                    reading_time=max(1, len(article_data.content.split()) // 200) if article_data.content else 1,
                )
                
                session.add(article_model)
                session.flush()
                
                # Handle categories if provided
                if hasattr(article_data, 'categories') and article_data.categories:
                    for category_name in article_data.categories:
                        category = session.query(CategoryModel).filter(
                            CategoryModel.name == category_name
                        ).first()
                        
                        if not category:
                            # Create category if it doesn't exist
                            category = CategoryModel(
                                name=category_name,
                                slug=category_name.lower().replace(' ', '-'),
                                is_active=True
                            )
                            session.add(category)
                            session.flush()
                        
                        article_model.categories.append(category)
                
                session.refresh(article_model)
                
                # Load relationships for response
                session.expunge(article_model)
                with get_db_session() as read_session:
                    article_with_relations = read_session.query(ArticleModel).options(
                        joinedload(ArticleModel.source),
                        joinedload(ArticleModel.categories)
                    ).filter(ArticleModel.id == article_model.id).first()
                    
                    return self._model_to_pydantic(article_with_relations)
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating article: {e}")
            raise DatabaseError(f"Failed to create article: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating article: {e}")
            raise DatabaseError(f"Failed to create article: {str(e)}")
    
    async def get_by_id(self, article_id: int, increment_view_count: bool = True) -> Optional[Article]:
        """
        Get article by ID.
        
        Args:
            article_id: Article ID
            increment_view_count: Whether to increment view count
            
        Returns:
            Optional[Article]: Article if found
        """
        try:
            with get_db_session() as session:
                query = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                ).filter(
                    ArticleModel.id == article_id,
                    not ArticleModel.is_archived
                )
                
                article_model = query.first()
                
                if not article_model:
                    return None
                
                # Increment view count if requested
                if increment_view_count:
                    with get_db_transaction() as write_session:
                        write_session.query(ArticleModel).filter(
                            ArticleModel.id == article_id
                        ).update({
                            ArticleModel.view_count: ArticleModel.view_count + 1
                        })
                    
                    # Refresh the model with updated view count
                    session.refresh(article_model)
                
                return self._model_to_pydantic(article_model)
                
        except Exception as e:
            logger.error(f"Error getting article by ID {article_id}: {e}")
            raise DatabaseError(f"Failed to get article: {str(e)}")
    
    async def get_by_url(self, url: str) -> Optional[Article]:
        """
        Get article by URL.
        
        Args:
            url: Article URL
            
        Returns:
            Optional[Article]: Article if found
        """
        try:
            with get_db_session() as session:
                article_model = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                ).filter(ArticleModel.url == url).first()
                
                if not article_model:
                    return None
                
                return self._model_to_pydantic(article_model)
                
        except Exception as e:
            logger.error(f"Error getting article by URL {url}: {e}")
            raise DatabaseError(f"Failed to get article: {str(e)}")
    
    async def update(self, article_id: int, update_data: ArticleUpdate) -> Article:
        """
        Update an article.
        
        Args:
            article_id: Article ID
            update_data: Update data
            
        Returns:
            Article: Updated article
            
        Raises:
            NotFoundError: If article not found
            DatabaseError: If update fails
        """
        try:
            with get_db_transaction() as session:
                article_model = session.query(ArticleModel).filter(
                    ArticleModel.id == article_id
                ).first()
                
                if not article_model:
                    raise NotFoundError(f"Article with ID {article_id} not found")
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    if hasattr(article_model, field):
                        setattr(article_model, field, value)
                
                # Update word count and reading time if content changed
                if update_data.content is not None:
                    article_model.word_count = len(update_data.content.split())
                    article_model.reading_time = max(1, article_model.word_count // 200)
                
                article_model.updated_at = datetime.now(timezone.utc)
                
                session.flush()
                session.refresh(article_model)
                
                # Load relationships for response
                article_with_relations = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                ).filter(ArticleModel.id == article_id).first()
                
                return self._model_to_pydantic(article_with_relations)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            raise DatabaseError(f"Failed to update article: {str(e)}")
    
    async def delete(self, article_id: int) -> bool:
        """
        Delete an article (soft delete by archiving).
        
        Args:
            article_id: Article ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            with get_db_transaction() as session:
                result = session.query(ArticleModel).filter(
                    ArticleModel.id == article_id
                ).update({
                    ArticleModel.is_archived: True,
                    ArticleModel.updated_at: datetime.now(timezone.utc)
                })
                
                return result > 0
                
        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            raise DatabaseError(f"Failed to delete article: {str(e)}")
    
    async def list_articles(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        source: Optional[str] = None,
        category: Optional[str] = None,
        archived: bool = False
    ) -> Tuple[List[Article], int]:
        """
        List articles with pagination and filtering.
        
        Args:
            limit: Maximum number of articles to return
            offset: Number of articles to skip
            source: Filter by source name
            category: Filter by category name
            archived: Include archived articles
            
        Returns:
            Tuple[List[Article], int]: Articles and total count
        """
        try:
            with get_db_session() as session:
                # Base query
                query = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                )
                
                # Filters
                filters = []
                if not archived:
                    filters.append(not ArticleModel.is_archived)
                
                if source:
                    query = query.join(SourceModel)
                    filters.append(SourceModel.name == source)
                
                if category:
                    query = query.join(ArticleModel.categories)
                    filters.append(CategoryModel.name == category)
                
                if filters:
                    query = query.filter(and_(*filters))
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                articles = query.order_by(desc(ArticleModel.created_at)).offset(offset).limit(limit).all()
                
                return [self._model_to_pydantic(article) for article in articles], total_count
                
        except Exception as e:
            logger.error(f"Error listing articles: {e}")
            raise DatabaseError(f"Failed to list articles: {str(e)}")
    
    async def search_articles(
        self, 
        query: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Article]:
        """
        Search articles by text.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Article]: Matching articles
        """
        try:
            with get_db_session() as session:
                search_filter = or_(
                    ArticleModel.title.ilike(f"%{query}%"),
                    ArticleModel.content.ilike(f"%{query}%"),
                    ArticleModel.summary.ilike(f"%{query}%")
                )
                
                articles = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                ).filter(
                    and_(
                        search_filter,
                        not ArticleModel.is_archived
                    )
                ).order_by(desc(ArticleModel.created_at)).offset(offset).limit(limit).all()
                
                return [self._model_to_pydantic(article) for article in articles]
                
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            raise DatabaseError(f"Failed to search articles: {str(e)}")
    
    async def get_articles_without_embeddings(self, limit: int = 100) -> List[Article]:
        """
        Get articles that don't have embeddings generated.
        
        Args:
            limit: Maximum number of articles
            
        Returns:
            List[Article]: Articles without embeddings
        """
        try:
            with get_db_session() as session:
                articles = session.query(ArticleModel).options(
                    joinedload(ArticleModel.source),
                    joinedload(ArticleModel.categories)
                ).filter(
                    and_(
                        not ArticleModel.embedding_generated,
                        not ArticleModel.is_archived
                    )
                ).order_by(asc(ArticleModel.created_at)).limit(limit).all()
                
                return [self._model_to_pydantic(article) for article in articles]
                
        except Exception as e:
            logger.error(f"Error getting articles without embeddings: {e}")
            raise DatabaseError(f"Failed to get articles without embeddings: {str(e)}")
    
    async def mark_embedding_generated(self, article_id: int) -> bool:
        """
        Mark article as having embedding generated.
        
        Args:
            article_id: Article ID
            
        Returns:
            bool: True if updated successfully
        """
        try:
            with get_db_transaction() as session:
                result = session.query(ArticleModel).filter(
                    ArticleModel.id == article_id
                ).update({
                    ArticleModel.embedding_generated: True,
                    ArticleModel.updated_at: datetime.now(timezone.utc)
                })
                
                return result > 0
                
        except Exception as e:
            logger.error(f"Error marking embedding generated for article {article_id}: {e}")
            raise DatabaseError(f"Failed to mark embedding generated: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get article statistics.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            with get_db_session() as session:
                total_articles = session.query(ArticleModel).filter(
                    not ArticleModel.is_archived
                ).count()
                
                articles_with_embeddings = session.query(ArticleModel).filter(
                    and_(
                        ArticleModel.embedding_generated,
                        not ArticleModel.is_archived
                    )
                ).count()
                
                articles_with_summaries = session.query(ArticleModel).filter(
                    and_(
                        ArticleModel.summary_generated,
                        not ArticleModel.is_archived
                    )
                ).count()
                
                # Get top sources
                top_sources = session.query(
                    SourceModel.name,
                    func.count(ArticleModel.id).label('count')
                ).join(ArticleModel).filter(
                    not ArticleModel.is_archived
                ).group_by(SourceModel.name).order_by(desc('count')).limit(5).all()
                
                return {
                    "total_articles": total_articles,
                    "articles_with_embeddings": articles_with_embeddings,
                    "articles_without_embeddings": total_articles - articles_with_embeddings,
                    "articles_with_summaries": articles_with_summaries,
                    "top_sources": {source.name: source.count for source in top_sources}
                }
                
        except Exception as e:
            logger.error(f"Error getting article stats: {e}")
            raise DatabaseError(f"Failed to get article stats: {str(e)}")
