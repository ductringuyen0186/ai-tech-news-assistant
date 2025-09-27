"""
Database Service
===============
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import hashlib

from ..core.config import settings
from ..models import Base, ArticleDB, Article, ArticleCreate, ArticleUpdate

logger = logging.getLogger(__name__)


class DatabaseService:
    """Production database service with connection pooling and error handling"""
    
    def __init__(self):
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise
    
    def create_article(self, article_data: ArticleCreate) -> Optional[Article]:
        """Create new article with duplicate handling"""
        session = self.get_session()
        
        try:
            # Generate unique ID from URL
            article_id = hashlib.sha256(str(article_data.url).encode()).hexdigest()[:16]
            
            # Check if article already exists
            existing = session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
            if existing:
                logger.debug(f"Article already exists: {article_id}")
                return self._db_to_pydantic(existing)
            
            # Create new article
            db_article = ArticleDB(
                id=article_id,
                title=article_data.title,
                content=article_data.content,
                url=str(article_data.url),
                published_at=article_data.published_at,
                source=article_data.source,
                source_id=article_data.source_id
            )
            
            session.add(db_article)
            session.commit()
            session.refresh(db_article)
            
            logger.debug(f"Created article: {article_id}")
            return self._db_to_pydantic(db_article)
            
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Article creation failed (duplicate): {e}")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating article: {e}")
            return None
        finally:
            session.close()
    
    def get_articles(
        self,
        limit: int = 20,
        offset: int = 0,
        source_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Article]:
        """Get articles with filtering and pagination"""
        session = self.get_session()
        
        try:
            query = session.query(ArticleDB)
            
            # Apply filters
            if source_filter:
                query = query.filter(ArticleDB.source.in_(source_filter))
            
            if date_from:
                query = query.filter(ArticleDB.published_at >= date_from)
            
            if date_to:
                query = query.filter(ArticleDB.published_at <= date_to)
            
            # Order by published date (newest first)
            query = query.order_by(desc(ArticleDB.published_at))
            
            # Apply pagination
            articles = query.offset(offset).limit(limit).all()
            
            return [self._db_to_pydantic(article) for article in articles]
            
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return []
        finally:
            session.close()
    
    def search_articles(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        source_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search articles with relevance scoring"""
        session = self.get_session()
        
        try:
            search_query = session.query(ArticleDB)
            
            # Apply source filter
            if source_filter:
                search_query = search_query.filter(ArticleDB.source.in_(source_filter))
            
            # Simple text search (can be enhanced with full-text search)
            search_terms = query.lower().split()
            conditions = []
            
            for term in search_terms:
                term_conditions = or_(
                    ArticleDB.title.ilike(f"%{term}%"),
                    ArticleDB.content.ilike(f"%{term}%")
                )
                conditions.append(term_conditions)
            
            if conditions:
                search_query = search_query.filter(and_(*conditions))
            
            # Order by relevance (title matches first, then content)
            articles = search_query.order_by(
                desc(ArticleDB.published_at)
            ).offset(offset).limit(limit).all()
            
            # Calculate relevance scores
            results = []
            for article in articles:
                score = self._calculate_relevance_score(article, query)
                results.append({
                    "article": self._db_to_pydantic(article),
                    "relevance_score": score,
                    "highlight_snippet": self._create_highlight_snippet(article, query)
                })
            
            # Sort by relevance score
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
        finally:
            session.close()
    
    def update_article_stats(self, article_id: str, view_increment: int = 0, summary_increment: int = 0):
        """Update article statistics"""
        session = self.get_session()
        
        try:
            article = session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
            if article:
                if view_increment > 0:
                    article.view_count += view_increment
                if summary_increment > 0:
                    article.summary_count += summary_increment
                
                session.commit()
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating article stats: {e}")
        finally:
            session.close()
    
    def get_article_count(self, source_filter: Optional[List[str]] = None) -> int:
        """Get total article count"""
        session = self.get_session()
        
        try:
            query = session.query(ArticleDB)
            
            if source_filter:
                query = query.filter(ArticleDB.source.in_(source_filter))
            
            return query.count()
            
        except Exception as e:
            logger.error(f"Error getting article count: {e}")
            return 0
        finally:
            session.close()
    
    def get_sources_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for each news source"""
        session = self.get_session()
        
        try:
            # Get article count per source
            source_stats = session.query(
                ArticleDB.source,
                func.count(ArticleDB.id).label('article_count'),
                func.max(ArticleDB.created_at).label('last_fetch'),
                func.avg(ArticleDB.view_count).label('avg_views')
            ).group_by(ArticleDB.source).all()
            
            results = []
            for stat in source_stats:
                results.append({
                    "name": stat.source,
                    "article_count": stat.article_count,
                    "last_fetch": stat.last_fetch,
                    "avg_views": stat.avg_views or 0.0
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting source stats: {e}")
            return []
        finally:
            session.close()
    
    def cleanup_old_articles(self, days_old: int = 30):
        """Remove articles older than specified days"""
        session = self.get_session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            deleted_count = session.query(ArticleDB).filter(
                ArticleDB.created_at < cutoff_date
            ).delete()
            
            session.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old articles")
            
            return deleted_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up articles: {e}")
            return 0
        finally:
            session.close()
    
    def _db_to_pydantic(self, db_article: ArticleDB) -> Article:
        """Convert SQLAlchemy model to Pydantic model"""
        return Article(
            id=db_article.id,
            title=db_article.title,
            content=db_article.content,
            url=db_article.url,
            published_at=db_article.published_at,
            source=db_article.source,
            source_id=db_article.source_id,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at,
            view_count=db_article.view_count,
            summary_count=db_article.summary_count,
            relevance_score=db_article.relevance_score,
            engagement_score=db_article.engagement_score
        )
    
    def _calculate_relevance_score(self, article: ArticleDB, query: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = query.lower()
        
        # Title matches get higher score
        if query_lower in article.title.lower():
            score += 10.0
        
        # Content matches get lower score
        if query_lower in article.content.lower():
            score += 5.0
        
        # Source popularity (can be enhanced)
        source_weights = {
            "Hacker News": 1.2,
            "Reddit Programming": 1.1,
            "GitHub Trending": 1.0
        }
        
        score *= source_weights.get(article.source, 1.0)
        
        # Recency bonus (newer articles get slight boost)
        days_old = (datetime.utcnow() - article.published_at).days
        if days_old < 7:
            score *= 1.1
        
        return round(score, 2)
    
    def _create_highlight_snippet(self, article: ArticleDB, query: str) -> str:
        """Create highlighted snippet for search results"""
        content = article.content
        query_lower = query.lower()
        
        # Find query in content
        content_lower = content.lower()
        index = content_lower.find(query_lower)
        
        if index != -1:
            start = max(0, index - 50)
            end = min(len(content), index + len(query) + 50)
            snippet = content[start:end]
            
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            
            return snippet
        
        # Return first part of content if query not found
        return content[:100] + "..." if len(content) > 100 else content


# Global database service instance
db_service = DatabaseService()