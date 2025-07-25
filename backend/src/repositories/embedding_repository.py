"""
Embedding Repository
==================

Data access layer for embedding operations.
Handles database interactions for embedding storage, retrieval, and similarity search.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import json
import numpy as np

from ..core.config import get_settings

settings = get_settings()
from ..core.exceptions import DatabaseError, NotFoundError
from ..models.embedding import SimilarityResult

logger = logging.getLogger(__name__)


class EmbeddingRepository:
    """
    Repository for embedding data access operations.
    
    This repository manages vector embeddings storage and retrieval,
    providing efficient similarity search capabilities and metadata management.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the embedding repository.
        
        Args:
            db_path: Optional database path. If None, uses configured path.
        """
        self.db_path = db_path or settings.database_path
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """Ensure embedding tables exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Main embeddings table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id TEXT NOT NULL,
                        content_type TEXT NOT NULL,  -- 'article', 'summary', etc.
                        embedding_vector TEXT NOT NULL,  -- JSON array of floats
                        model_name TEXT NOT NULL,
                        embedding_dim INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,  -- JSON object for additional info
                        UNIQUE(content_id, content_type, model_name)
                    )
                """)
                
                # Embedding metadata table for efficient search
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS embedding_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        embedding_id INTEGER NOT NULL,
                        title TEXT,
                        content_snippet TEXT,
                        source TEXT,
                        published_at TIMESTAMP,
                        additional_metadata TEXT,  -- JSON object
                        FOREIGN KEY(embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_content ON embeddings(content_id, content_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON embeddings(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_embedding_metadata_source ON embedding_metadata(source)")
                
                conn.commit()
                logger.debug("Embedding tables initialized")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize embedding tables: {e}")
            raise DatabaseError(f"Table initialization failed: {str(e)}")
    
    async def store_embedding(
        self,
        content_id: str,
        content_type: str,
        embedding_vector: List[float],
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store an embedding vector with associated metadata.
        
        Args:
            content_id: Identifier for the content (e.g., article ID)
            content_type: Type of content ('article', 'summary', etc.)
            embedding_vector: The embedding vector
            model_name: Name of the model used to generate embedding
            metadata: Optional metadata dictionary
            
        Returns:
            ID of the stored embedding
            
        Raises:
            DatabaseError: If storage fails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Convert embedding to JSON string
                embedding_json = json.dumps(embedding_vector)
                embedding_dim = len(embedding_vector)
                
                # Insert or replace embedding
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO embeddings (
                        content_id, content_type, embedding_vector, 
                        model_name, embedding_dim, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    content_id,
                    content_type,
                    embedding_json,
                    model_name,
                    embedding_dim,
                    json.dumps(metadata) if metadata else None
                ))
                
                embedding_id = cursor.lastrowid
                
                # Store searchable metadata if provided
                if metadata:
                    await self._store_embedding_metadata(conn, embedding_id, metadata)
                
                conn.commit()
                logger.debug(f"Stored embedding for {content_type}:{content_id}")
                return embedding_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to store embedding: {e}")
            raise DatabaseError(f"Embedding storage failed: {str(e)}")
    
    async def _store_embedding_metadata(
        self,
        conn: sqlite3.Connection,
        embedding_id: int,
        metadata: Dict[str, Any]
    ) -> None:
        """Store searchable metadata for an embedding."""
        conn.execute("""
            INSERT OR REPLACE INTO embedding_metadata (
                embedding_id, title, content_snippet, source, 
                published_at, additional_metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            embedding_id,
            metadata.get("title"),
            metadata.get("content_snippet"),
            metadata.get("source"),
            metadata.get("published_at"),
            json.dumps({k: v for k, v in metadata.items() 
                       if k not in ["title", "content_snippet", "source", "published_at"]})
        ))
    
    async def get_embedding(
        self,
        content_id: str,
        content_type: str,
        model_name: str
    ) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve an embedding vector for specific content.
        
        Args:
            content_id: Content identifier
            content_type: Type of content
            model_name: Model name used for embedding
            
        Returns:
            Tuple of (embedding_vector, metadata) if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                row = conn.execute("""
                    SELECT embedding_vector, metadata FROM embeddings
                    WHERE content_id = ? AND content_type = ? AND model_name = ?
                """, (content_id, content_type, model_name)).fetchone()
                
                if not row:
                    return None
                
                embedding_vector = json.loads(row["embedding_vector"])
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                
                return embedding_vector, metadata
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get embedding: {e}")
            raise DatabaseError(f"Embedding retrieval failed: {str(e)}")
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        model_name: str,
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        content_type: Optional[str] = None
    ) -> List[SimilarityResult]:
        """
        Perform similarity search using embedding vectors.
        
        Args:
            query_embedding: Query embedding vector
            model_name: Model name to search within
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score
            content_type: Optional filter by content type
            
        Returns:
            List of similarity results sorted by score
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query with optional content type filter
                where_conditions = ["e.model_name = ?"]
                where_values = [model_name]
                
                if content_type:
                    where_conditions.append("e.content_type = ?")
                    where_values.append(content_type)
                
                where_clause = " AND ".join(where_conditions)
                
                # Get all embeddings for comparison
                query = f"""
                    SELECT e.content_id, e.content_type, e.embedding_vector, e.metadata,
                           m.title, m.content_snippet, m.source, m.additional_metadata
                    FROM embeddings e
                    LEFT JOIN embedding_metadata m ON e.id = m.embedding_id
                    WHERE {where_clause}
                """
                
                rows = conn.execute(query, where_values).fetchall()
                
                if not rows:
                    return []
                
                # Compute similarities
                similarities = []
                query_vector = np.array(query_embedding)
                
                for row in rows:
                    try:
                        candidate_vector = np.array(json.loads(row["embedding_vector"]))
                        
                        # Compute cosine similarity
                        similarity = self._cosine_similarity(query_vector, candidate_vector)
                        
                        if similarity >= similarity_threshold:
                            # Combine metadata from both tables
                            metadata = {}
                            if row["metadata"]:
                                metadata.update(json.loads(row["metadata"]))
                            if row["additional_metadata"]:
                                metadata.update(json.loads(row["additional_metadata"]))
                            
                            # Add searchable fields to metadata
                            if row["title"]:
                                metadata["title"] = row["title"]
                            if row["source"]:
                                metadata["source"] = row["source"]
                            
                            similarities.append(SimilarityResult(
                                id=f"{row['content_type']}:{row['content_id']}",
                                similarity_score=float(similarity),
                                metadata=metadata,
                                content_snippet=row["content_snippet"]
                            ))
                            
                    except Exception as e:
                        logger.warning(f"Failed to compute similarity for {row['content_id']}: {e}")
                        continue
                
                # Sort by similarity score and return top_k
                similarities.sort(key=lambda x: x.similarity_score, reverse=True)
                return similarities[:top_k]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise DatabaseError(f"Similarity search failed: {str(e)}")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_embeddings(
        self,
        content_id: str,
        content_type: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> int:
        """
        Delete embeddings for specific content.
        
        Args:
            content_id: Content identifier
            content_type: Optional content type filter
            model_name: Optional model name filter
            
        Returns:
            Number of deleted embeddings
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                where_conditions = ["content_id = ?"]
                where_values = [content_id]
                
                if content_type:
                    where_conditions.append("content_type = ?")
                    where_values.append(content_type)
                
                if model_name:
                    where_conditions.append("model_name = ?")
                    where_values.append(model_name)
                
                where_clause = " AND ".join(where_conditions)
                
                cursor = conn.execute(f"""
                    DELETE FROM embeddings WHERE {where_clause}
                """, where_values)
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.debug(f"Deleted {deleted_count} embeddings for {content_id}")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete embeddings: {e}")
            raise DatabaseError(f"Embedding deletion failed: {str(e)}")
    
    async def get_embeddings_by_content_type(
        self,
        content_type: str,
        model_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get embeddings by content type.
        
        Args:
            content_type: Type of content to retrieve
            model_name: Model name filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of embedding records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                rows = conn.execute("""
                    SELECT e.content_id, e.content_type, e.embedding_dim, 
                           e.created_at, e.metadata,
                           m.title, m.content_snippet, m.source
                    FROM embeddings e
                    LEFT JOIN embedding_metadata m ON e.id = m.embedding_id
                    WHERE e.content_type = ? AND e.model_name = ?
                    ORDER BY e.created_at DESC
                    LIMIT ? OFFSET ?
                """, (content_type, model_name, limit, offset)).fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get embeddings by content type: {e}")
            raise DatabaseError(f"Query failed: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get embedding statistics.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total embeddings
                total = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
                
                # By content type
                by_type = conn.execute("""
                    SELECT content_type, COUNT(*) as count
                    FROM embeddings
                    GROUP BY content_type
                    ORDER BY count DESC
                """).fetchall()
                
                # By model
                by_model = conn.execute("""
                    SELECT model_name, COUNT(*) as count
                    FROM embeddings
                    GROUP BY model_name
                    ORDER BY count DESC
                """).fetchall()
                
                # Average dimension
                avg_dim = conn.execute("""
                    SELECT AVG(embedding_dim) FROM embeddings
                """).fetchone()[0] or 0
                
                # Storage estimate (rough calculation)
                storage_mb = (total * avg_dim * 4) / (1024 * 1024)  # 4 bytes per float
                
                return {
                    "total_embeddings": total,
                    "by_content_type": [{"type": row[0], "count": row[1]} for row in by_type],
                    "by_model": [{"model": row[0], "count": row[1]} for row in by_model],
                    "average_dimension": float(avg_dim),
                    "estimated_storage_mb": storage_mb
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get embedding stats: {e}")
            raise DatabaseError(f"Stats query failed: {str(e)}")
    
    async def cleanup_orphaned_metadata(self) -> int:
        """
        Clean up orphaned embedding metadata.
        
        Returns:
            Number of cleaned up records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM embedding_metadata 
                    WHERE embedding_id NOT IN (SELECT id FROM embeddings)
                """)
                
                cleaned_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {cleaned_count} orphaned metadata records")
                return cleaned_count
                
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup orphaned metadata: {e}")
            raise DatabaseError(f"Cleanup failed: {str(e)}")
