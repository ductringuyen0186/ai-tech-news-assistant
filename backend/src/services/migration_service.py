"""
Database Migration Service
=========================

Service to handle migration from SQLite repositories to SQLAlchemy ORM.
Provides data migration utilities and compatibility layers.
"""

import logging
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from ..database.session import get_db_session, get_db_transaction
from ..database.models import (
    Article as ArticleModel,
    Source as SourceModel, 
    Category as CategoryModel,
    Embedding as EmbeddingModel,
    serialize_embedding,
    deserialize_embedding
)
from ..repositories.sqlalchemy_repository import SQLAlchemyArticleRepository
from ..models.article import ArticleCreate
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseMigrationService:
    """
    Service for migrating data from SQLite to SQLAlchemy ORM.
    """
    
    def __init__(self, old_db_path: Optional[str] = None):
        """
        Initialize migration service.
        
        Args:
            old_db_path: Path to the old SQLite database
        """
        self.old_db_path = old_db_path or "./data/ai_news.db"
        self.sqlalchemy_repo = SQLAlchemyArticleRepository()
    
    def check_old_database_exists(self) -> bool:
        """Check if old SQLite database exists."""
        try:
            with sqlite3.connect(self.old_db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def get_old_articles_count(self) -> int:
        """Get count of articles in old database."""
        try:
            with sqlite3.connect(self.old_db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting old articles count: {e}")
            return 0
    
    def migrate_sources(self) -> int:
        """
        Migrate sources from old database.
        
        Returns:
            int: Number of sources migrated
        """
        migrated_count = 0
        
        try:
            # Get unique sources from old articles table
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_conn.row_factory = sqlite3.Row
                cursor = old_conn.execute("""
                    SELECT DISTINCT source, COUNT(*) as article_count 
                    FROM articles 
                    WHERE source IS NOT NULL AND source != '' 
                    GROUP BY source
                """)
                sources = cursor.fetchall()
            
            # Insert sources into new database
            with get_db_transaction() as session:
                for source_row in sources:
                    source_name = source_row["source"]
                    
                    # Check if source already exists
                    existing = session.query(SourceModel).filter(
                        SourceModel.name == source_name
                    ).first()
                    
                    if not existing:
                        new_source = SourceModel(
                            name=source_name,
                            url=f"https://{source_name.lower().replace(' ', '')}.com",  # Placeholder URL
                            description=f"News source: {source_name}",
                            is_active=True,
                            scrape_frequency=3600,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        session.add(new_source)
                        migrated_count += 1
                        logger.info(f"Migrated source: {source_name}")
            
            logger.info(f"Migrated {migrated_count} sources")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating sources: {e}")
            raise
    
    def migrate_categories(self) -> int:
        """
        Migrate categories from old database.
        
        Returns:
            int: Number of categories migrated
        """
        migrated_count = 0
        
        try:
            # Get categories from old articles table
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_conn.row_factory = sqlite3.Row
                cursor = old_conn.execute("""
                    SELECT DISTINCT categories 
                    FROM articles 
                    WHERE categories IS NOT NULL AND categories != ''
                """)
                category_rows = cursor.fetchall()
            
            # Extract unique categories
            unique_categories = set()
            for row in category_rows:
                if row["categories"]:
                    try:
                        import json
                        categories_list = json.loads(row["categories"])
                        if isinstance(categories_list, list):
                            unique_categories.update(categories_list)
                    except (json.JSONDecodeError, TypeError):
                        # Handle plain text categories
                        unique_categories.add(row["categories"])
            
            # Insert categories into new database
            with get_db_transaction() as session:
                for category_name in unique_categories:
                    if category_name and isinstance(category_name, str):
                        # Check if category already exists
                        existing = session.query(CategoryModel).filter(
                            CategoryModel.name == category_name
                        ).first()
                        
                        if not existing:
                            slug = category_name.lower().replace(' ', '-').replace('_', '-')
                            new_category = CategoryModel(
                                name=category_name,
                                slug=slug,
                                description=f"Category: {category_name}",
                                is_active=True,
                                created_at=datetime.now(timezone.utc)
                            )
                            session.add(new_category)
                            migrated_count += 1
                            logger.info(f"Migrated category: {category_name}")
            
            logger.info(f"Migrated {migrated_count} categories")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating categories: {e}")
            raise
    
    def migrate_articles(self, batch_size: int = 100) -> int:
        """
        Migrate articles from old database.
        
        Args:
            batch_size: Number of articles to process in each batch
            
        Returns:
            int: Number of articles migrated
        """
        migrated_count = 0
        
        try:
            # Get total count for progress tracking
            total_articles = self.get_old_articles_count()
            logger.info(f"Starting migration of {total_articles} articles")
            
            offset = 0
            while True:
                # Get batch of articles from old database
                with sqlite3.connect(self.old_db_path) as old_conn:
                    old_conn.row_factory = sqlite3.Row
                    cursor = old_conn.execute("""
                        SELECT * FROM articles 
                        ORDER BY id 
                        LIMIT ? OFFSET ?
                    """, (batch_size, offset))
                    articles = cursor.fetchall()
                
                if not articles:
                    break
                
                # Process batch
                batch_migrated = 0
                with get_db_transaction() as session:
                    for old_article in articles:
                        try:
                            # Check if article already exists
                            existing = session.query(ArticleModel).filter(
                                ArticleModel.url == old_article["url"]
                            ).first()
                            
                            if existing:
                                continue
                            
                            # Get or create source
                            source = None
                            if old_article["source"]:
                                source = session.query(SourceModel).filter(
                                    SourceModel.name == old_article["source"]
                                ).first()
                            
                            # Create new article
                            new_article = ArticleModel(
                                title=old_article["title"],
                                url=old_article["url"],
                                content=old_article["content"],
                                summary=old_article["summary"],
                                author=old_article["author"],
                                published_at=self._parse_datetime(old_article["published_at"]),
                                created_at=self._parse_datetime(old_article["created_at"]) or datetime.now(timezone.utc),
                                updated_at=self._parse_datetime(old_article["updated_at"]) or datetime.now(timezone.utc),
                                source_id=source.id if source else None,
                                language='en',
                                is_archived=bool(old_article.get("is_archived", False)),
                                view_count=old_article.get("view_count", 0),
                                embedding_generated=bool(old_article.get("embedding_generated", False)),
                                summary_generated=bool(old_article.get("summary") is not None),
                                metadata=self._parse_json(old_article.get("metadata")),
                                word_count=len(old_article["content"].split()) if old_article["content"] else 0,
                            )
                            
                            # Set reading time
                            new_article.reading_time = max(1, new_article.word_count // 200) if new_article.word_count > 0 else 1
                            
                            session.add(new_article)
                            session.flush()  # Get the ID
                            
                            # Handle categories
                            if old_article.get("categories"):
                                categories = self._parse_categories(old_article["categories"])
                                for category_name in categories:
                                    category = session.query(CategoryModel).filter(
                                        CategoryModel.name == category_name
                                    ).first()
                                    if category:
                                        new_article.categories.append(category)
                            
                            batch_migrated += 1
                            
                        except Exception as e:
                            logger.error(f"Error migrating article {old_article['id']}: {e}")
                            continue
                
                migrated_count += batch_migrated
                offset += batch_size
                
                logger.info(f"Migrated batch: {batch_migrated} articles (Total: {migrated_count}/{total_articles})")
            
            logger.info(f"Successfully migrated {migrated_count} articles")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating articles: {e}")
            raise
    
    def migrate_embeddings(self, batch_size: int = 50) -> int:
        """
        Migrate embeddings from old database if they exist.
        
        Args:
            batch_size: Number of embeddings to process in each batch
            
        Returns:
            int: Number of embeddings migrated
        """
        migrated_count = 0
        
        try:
            # Check if embeddings table exists
            with sqlite3.connect(self.old_db_path) as old_conn:
                cursor = old_conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='embeddings'
                """)
                if not cursor.fetchone():
                    logger.info("No embeddings table found in old database")
                    return 0
            
            # Get embeddings
            with sqlite3.connect(self.old_db_path) as old_conn:
                old_conn.row_factory = sqlite3.Row
                cursor = old_conn.execute("SELECT * FROM embeddings")
                embeddings = cursor.fetchall()
            
            logger.info(f"Found {len(embeddings)} embeddings to migrate")
            
            # Process embeddings in batches
            for i in range(0, len(embeddings), batch_size):
                batch = embeddings[i:i + batch_size]
                
                with get_db_transaction() as session:
                    for old_embedding in batch:
                        try:
                            # Find corresponding article in new database
                            article = session.query(ArticleModel).filter(
                                ArticleModel.id == old_embedding["article_id"]
                            ).first()
                            
                            if not article:
                                logger.warning(f"Article {old_embedding['article_id']} not found for embedding {old_embedding['id']}")
                                continue
                            
                            # Check if embedding already exists
                            existing = session.query(EmbeddingModel).filter(
                                EmbeddingModel.article_id == article.id,
                                EmbeddingModel.embedding_model == old_embedding.get("embedding_model", "unknown"),
                                EmbeddingModel.content_type == old_embedding.get("content_type", "full_content")
                            ).first()
                            
                            if existing:
                                continue
                            
                            # Create new embedding
                            new_embedding = EmbeddingModel(
                                article_id=article.id,
                                embedding_vector=old_embedding["embedding_vector"],
                                embedding_model=old_embedding.get("embedding_model", "unknown"),
                                embedding_dim=old_embedding.get("embedding_dim", 384),
                                content_type=old_embedding.get("content_type", "full_content"),
                                chunk_index=old_embedding.get("chunk_index", 0),
                                created_at=self._parse_datetime(old_embedding.get("created_at")) or datetime.now(timezone.utc),
                                processing_time=old_embedding.get("processing_time"),
                                metadata=self._parse_json(old_embedding.get("metadata"))
                            )
                            
                            session.add(new_embedding)
                            migrated_count += 1
                            
                        except Exception as e:
                            logger.error(f"Error migrating embedding {old_embedding['id']}: {e}")
                            continue
                
                logger.info(f"Migrated batch: {len(batch)} embeddings (Total: {migrated_count})")
            
            logger.info(f"Successfully migrated {migrated_count} embeddings")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating embeddings: {e}")
            raise
    
    def run_full_migration(self) -> Dict[str, int]:
        """
        Run complete migration from old database to new SQLAlchemy database.
        
        Returns:
            Dict[str, int]: Migration results
        """
        results = {
            "sources": 0,
            "categories": 0,
            "articles": 0,
            "embeddings": 0
        }
        
        try:
            if not self.check_old_database_exists():
                logger.warning("Old database not found, skipping migration")
                return results
            
            logger.info("Starting full database migration")
            
            # Initialize new database
            from ..database.base import init_db
            init_db()
            
            # Migrate in order (respecting foreign key dependencies)
            results["sources"] = self.migrate_sources()
            results["categories"] = self.migrate_categories()
            results["articles"] = self.migrate_articles()
            results["embeddings"] = self.migrate_embeddings()
            
            logger.info(f"Migration completed successfully: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None
        
        try:
            # Try different datetime formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse datetime: {datetime_str}")
            return None
            
        except Exception:
            return None
    
    def _parse_json(self, json_str: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse JSON string to dictionary."""
        if not json_str:
            return None
        
        try:
            import json
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def _parse_categories(self, categories_str: str) -> List[str]:
        """Parse categories string to list."""
        if not categories_str:
            return []
        
        try:
            import json
            parsed = json.loads(categories_str)
            if isinstance(parsed, list):
                return [str(cat) for cat in parsed if cat]
            else:
                return [str(parsed)] if parsed else []
        except (json.JSONDecodeError, TypeError):
            # Handle plain text categories
            return [categories_str.strip()] if categories_str.strip() else []


def run_migration_if_needed() -> bool:
    """
    Run migration if old database exists and new database is empty.
    
    Returns:
        bool: True if migration was run
    """
    try:
        migration_service = DatabaseMigrationService()
        
        # Check if old database exists
        if not migration_service.check_old_database_exists():
            logger.info("No old database found, skipping migration")
            return False
        
        # Check if new database is empty
        with get_db_session() as session:
            article_count = session.query(ArticleModel).count()
            if article_count > 0:
                logger.info("New database already has data, skipping migration")
                return False
        
        # Run migration
        logger.info("Running automatic database migration")
        results = migration_service.run_full_migration()
        logger.info(f"Migration completed: {results}")
        return True
        
    except Exception as e:
        logger.error(f"Automatic migration failed: {e}")
        return False
