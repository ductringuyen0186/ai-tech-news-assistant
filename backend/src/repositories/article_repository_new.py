"""
Article Repository
================

Repository for managing article data in SQLite database.
"""

import sqlite3
import json

from ..models.article import Article, ArticleUpdate
from ..core.exceptions import DatabaseError, NotFoundError


class ArticleRepository:
    """Repository for article data access operations."""
    
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = db_path
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    content TEXT,
                    summary TEXT,
                    author TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    categories TEXT,
                    metadata TEXT,
                    is_archived BOOLEAN DEFAULT FALSE,
                    view_count INTEGER DEFAULT 0,
                    embedding_generated BOOLEAN DEFAULT FALSE
                )
            """)
    
    def _row_to_article(self, row):
        if not row:
            return None
        
        # Parse JSON fields safely
        categories = None
        if row["categories"]:
            try:
                categories = json.loads(row["categories"])
            except (json.JSONDecodeError, TypeError):
                categories = None
        
        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except (json.JSONDecodeError, TypeError):
                metadata = None
        
        return Article(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            content=row["content"],
            summary=row["summary"],
            source=row["source"],
            author=row["author"],
            published_at=row["published_at"],
            categories=categories,
            metadata=metadata,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_archived=bool(row["is_archived"]),
            view_count=row["view_count"] or 0,
            embedding_generated=bool(row["embedding_generated"]),
            published_date=row["published_at"]
        )
    
    async def create(self, article):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            existing = conn.execute("SELECT id FROM articles WHERE url = ?", (article.url,)).fetchone()
            if existing:
                raise DatabaseError(f"Article with URL already exists: {article.url}")
            cursor = conn.execute("""
                INSERT INTO articles (title, url, content, author, published_at, source, categories, metadata) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (article.title, article.url, article.content, 
                  getattr(article, "author", None), 
                  getattr(article, "published_at", None) or getattr(article, "published_date", None), 
                  article.source, 
                  json.dumps(getattr(article, "categories", None)) if getattr(article, "categories", None) else None, 
                  json.dumps(getattr(article, "metadata", None)) if getattr(article, "metadata", None) else None))
            article_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
            return self._row_to_article(row)
    
    async def get_by_id(self, article_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Increment view count
            conn.execute("UPDATE articles SET view_count = view_count + 1 WHERE id = ?", (article_id,))
            row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
            if not row:
                raise NotFoundError(f"Article with id {article_id} not found")
            return self._row_to_article(row)
    
    async def get_by_url(self, url: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM articles WHERE url = ?", (url,)).fetchone()
            return self._row_to_article(row)
    
    async def update(self, article_id: int, update_data: ArticleUpdate):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Check if article exists
            existing = conn.execute("SELECT id FROM articles WHERE id = ?", (article_id,)).fetchone()
            if not existing:
                raise NotFoundError(f"Article with id {article_id} not found")
            
            # Build update query dynamically
            update_fields = []
            update_values = []
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                update_fields.append(f"{field} = ?")
                update_values.append(value)
            
            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE articles SET {', '.join(update_fields)} WHERE id = ?"
                update_values.append(article_id)
                conn.execute(query, update_values)
            
            # Return updated article
            row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
            return self._row_to_article(row)
    
    async def delete(self, article_id: int):
        with sqlite3.connect(self.db_path) as conn:
            # Check if article exists
            existing = conn.execute("SELECT id FROM articles WHERE id = ?", (article_id,)).fetchone()
            if not existing:
                raise NotFoundError(f"Article with id {article_id} not found")
            
            # Soft delete by setting is_archived = True
            cursor = conn.execute("UPDATE articles SET is_archived = TRUE WHERE id = ?", (article_id,))
            return cursor.rowcount > 0
    
    async def list_articles(self, limit=50, offset=0, source=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build query with optional source filter
            base_query = "FROM articles WHERE is_archived = FALSE"
            params = []
            
            if source:
                base_query += " AND source = ?"
                params.append(source)
            
            # Get total count
            count_query = f"SELECT COUNT(*) as count {base_query}"
            total_count = conn.execute(count_query, params).fetchone()["count"]
            
            # Get articles with pagination
            query = f"SELECT * {base_query} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(query, params).fetchall()
            articles = [self._row_to_article(row) for row in rows]
            
            return articles, total_count
    
    async def search_articles(self, query, limit=50, offset=0):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            search_query = "SELECT * FROM articles WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            search_term = f"%{query}%"
            rows = conn.execute(search_query, (search_term, search_term, limit, offset)).fetchall()
            return [self._row_to_article(row) for row in rows]
    
    async def get_articles_without_embeddings(self, limit=100):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM articles WHERE embedding_generated = FALSE ORDER BY created_at ASC LIMIT ?", (limit,)).fetchall()
            return [self._row_to_article(row) for row in rows]
    
    async def mark_embedding_generated(self, article_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE articles SET embedding_generated = TRUE WHERE id = ?", (article_id,))
            return cursor.rowcount > 0
    
    async def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as count FROM articles").fetchone()["count"]
            with_embeddings = conn.execute("SELECT COUNT(*) as count FROM articles WHERE embedding_generated = TRUE").fetchone()["count"]
            with_summaries = conn.execute("SELECT COUNT(*) as count FROM articles WHERE summary IS NOT NULL AND summary != ''").fetchone()["count"]
            
            # Get top sources
            top_sources_rows = conn.execute("SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC LIMIT 5").fetchall()
            top_sources = {row["source"]: row["count"] for row in top_sources_rows}
            
            return {
                "total_articles": total,
                "articles_with_embeddings": with_embeddings,
                "articles_without_embeddings": total - with_embeddings,
                "articles_with_summaries": with_summaries,
                "top_sources": top_sources
            }
