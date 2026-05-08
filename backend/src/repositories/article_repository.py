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
        # Handle both SQLAlchemy URL format and direct file paths
        if db_path.startswith('sqlite:///'):
            # Convert SQLAlchemy format to file path
            # sqlite:///:memory: -> :memory:
            # sqlite:///./path/to/db.db -> ./path/to/db.db
            self.db_path = db_path.replace('sqlite:///', '')
        else:
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
                    embedding_generated BOOLEAN DEFAULT FALSE,
                    summary_generated BOOLEAN DEFAULT FALSE
                )
            """)
            # Lightweight migration: older DBs may be missing summary_generated.
            existing_cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(articles)").fetchall()
            }
            if "summary_generated" not in existing_cols:
                conn.execute(
                    "ALTER TABLE articles ADD COLUMN summary_generated "
                    "BOOLEAN DEFAULT FALSE"
                )
            if "summary" not in existing_cols:
                conn.execute("ALTER TABLE articles ADD COLUMN summary TEXT")
            if "image_url" not in existing_cols:
                # Hero/thumbnail URL extracted from RSS feed media tags.
                # Frontend NewsCard falls back to a placeholder when null.
                conn.execute("ALTER TABLE articles ADD COLUMN image_url TEXT")
    
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
        
        # `summary_generated` may not exist on legacy rows fetched before the
        # ALTER TABLE migration ran on the connected DB; default to False.
        try:
            summary_generated = bool(row["summary_generated"])
        except (IndexError, KeyError):
            summary_generated = False

        # ``image_url`` was added later via lightweight ALTER TABLE; older
        # rows may simply not have the column populated. Read defensively.
        try:
            image_url = row["image_url"]
        except (IndexError, KeyError):
            image_url = None

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
            image_url=image_url,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_archived=bool(row["is_archived"]),
            view_count=row["view_count"] or 0,
            embedding_generated=bool(row["embedding_generated"]),
            summary_generated=summary_generated,
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
            # Only get non-archived articles and increment view count
            conn.execute("UPDATE articles SET view_count = view_count + 1 WHERE id = ? AND is_archived = FALSE", (article_id,))
            row = conn.execute("SELECT * FROM articles WHERE id = ? AND is_archived = FALSE", (article_id,)).fetchone()
            if not row:
                raise NotFoundError(f"Article with id {article_id} not found")
            return self._row_to_article(row)
    
    async def get_summary_only(self, article_id: int):
        """Fast cache-lookup helper: returns ``articles.summary`` for the
        given id, or ``None`` if no row matches or the column is empty.

        This is the read-side primitive used by the ``summarize_article``
        agent skill (Mission 2, M2) before deciding whether to call the
        LLM. It is deliberately cheap: a single ``SELECT summary`` with no
        view-count side-effect, so it's safe to call from inside a tight
        agent loop.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT summary FROM articles WHERE id = ?",
                (article_id,),
            ).fetchone()
        if not row:
            return None
        summary = row[0]
        if summary is None:
            return None
        if isinstance(summary, str) and not summary.strip():
            return None
        return summary

    async def get_content_only(self, article_id: int):
        """Read the article body for summarization.

        Mirrors :meth:`get_summary_only` but returns the ``content`` field
        (full body), or ``None`` when the article has no usable body.
        Used by ``summarize_article`` on cache miss to feed the LLM.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT title, content FROM articles WHERE id = ?",
                (article_id,),
            ).fetchone()
        if not row:
            return None
        body = (row["content"] or "").strip()
        if not body:
            # Fall back to title alone -- better than nothing for short feed items.
            title = (row["title"] or "").strip()
            return title or None
        return body
    
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
    
    async def list_articles(self, limit=50, offset=0, source=None, categories=None):
        """List non-archived articles, optionally filtered by source and/or
        category tags.

        ``categories`` is an iterable of category names to match against the
        article's stored ``categories`` JSON-array column. Matching is OR-ed
        across the supplied values (an article needs to have ANY of the
        listed categories to match) and is implemented with a JSON LIKE
        pattern that anchors on the quoted token so substring collisions
        (e.g. "AI" matching "AI/ML") don't false-positive.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query with optional source + category filters
            base_query = "FROM articles WHERE is_archived = FALSE"
            params: list = []

            if source:
                base_query += " AND source = ?"
                params.append(source)

            # Categories are stored as a JSON array string (e.g.
            # '["AI/ML"]'). We match on the exact quoted token so "AI"
            # doesn't accidentally match "AI/ML" via substring.
            cat_list = [c for c in (categories or []) if c]
            if cat_list:
                clauses = []
                for c in cat_list:
                    clauses.append("categories LIKE ?")
                    params.append(f'%"{c}"%')
                base_query += " AND (" + " OR ".join(clauses) + ")"

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

    async def get_articles_without_summary(self, limit: int = 100):
        """
        Return articles still needing an AI summary (excludes archived).

        We trust `summary_generated` as the source of truth: articles whose
        content was too short to summarize are still marked TRUE so we don't
        re-process them on every run.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM articles "
                "WHERE is_archived = FALSE "
                "  AND summary_generated = FALSE "
                "ORDER BY created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._row_to_article(row) for row in rows]

    async def mark_summary_generated(self, article_id, summary=None):
        """Flip summary_generated to TRUE; optionally write the summary text."""
        with sqlite3.connect(self.db_path) as conn:
            if summary is not None:
                cursor = conn.execute(
                    "UPDATE articles SET summary = ?, summary_generated = TRUE, "
                    "    updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (summary, article_id),
                )
            else:
                cursor = conn.execute(
                    "UPDATE articles SET summary_generated = TRUE, "
                    "    updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (article_id,),
                )
            return cursor.rowcount > 0

    async def get_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as count FROM articles").fetchone()["count"]
            with_embeddings = conn.execute("SELECT COUNT(*) as count FROM articles WHERE embedding_generated = TRUE").fetchone()["count"]
            with_summaries = conn.execute("SELECT COUNT(*) as count FROM articles WHERE summary IS NOT NULL AND TRIM(summary) != ''").fetchone()["count"]

            top_sources_rows = conn.execute("SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC LIMIT 5").fetchall()
            top_sources = {row["source"]: row["count"] for row in top_sources_rows}

            return {
                "total_articles": total,
                "articles_with_embeddings": with_embeddings,
                "articles_without_embeddings": total - with_embeddings,
                "articles_with_summaries": with_summaries,
                "articles_without_summaries": total - with_summaries,
                "top_sources": top_sources,
            }
