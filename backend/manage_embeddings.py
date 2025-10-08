"""
Article Embedding Management Script
==================================

This script provides utilities to generate and manage embeddings for articles
stored in the SQLite database. It can process existing articles and add
embedding data for RAG functionality.
"""

import asyncio
import sqlite3
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vectorstore.embeddings import EmbeddingGenerator
from utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_PATH = "./data/articles.db"


class ArticleEmbeddingManager:
    """Manager for article embedding operations."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize the embedding manager.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = Path(db_path)
        self.embedding_generator = EmbeddingGenerator()
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {db_path}")
        
        logger.info(f"Embedding manager initialized with database: {db_path}")
    
    async def setup_database(self) -> None:
        """Set up the database schema for embeddings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if embedding columns exist
            cursor.execute("PRAGMA table_info(articles)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add embedding columns if they don't exist
            if "embedding" not in columns:
                logger.info("Adding embedding column to articles table")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN embedding TEXT
                """)
            
            if "embedding_model" not in columns:
                logger.info("Adding embedding_model column to articles table")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN embedding_model TEXT
                """)
            
            if "embedding_dim" not in columns:
                logger.info("Adding embedding_dim column to articles table")
                cursor.execute("""
                    ALTER TABLE articles 
                    ADD COLUMN embedding_dim INTEGER
                """)
            
            conn.commit()
            logger.info("Database schema updated for embeddings")
    
    async def get_articles_without_embeddings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get articles that don't have embeddings yet.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            query = """
                SELECT id, title, content, description as summary, source, url, published_date
                FROM articles 
                WHERE embedding IS NULL
                ORDER BY published_date DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                article = dict(row)
                articles.append(article)
            
            logger.info(f"Found {len(articles)} articles without embeddings")
            return articles
    
    async def get_embedding_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings in the database.
        
        Returns:
            Statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Articles with embeddings
            cursor.execute("SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL")
            embedded_articles = cursor.fetchone()[0]
            
            # Articles with content but no embeddings
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE content IS NOT NULL AND embedding IS NULL
            """)
            pending_articles = cursor.fetchone()[0]
            
            # Embedding models used
            cursor.execute("""
                SELECT embedding_model, COUNT(*) 
                FROM articles 
                WHERE embedding_model IS NOT NULL 
                GROUP BY embedding_model
            """)
            model_stats = dict(cursor.fetchall())
            
            return {
                "total_articles": total_articles,
                "embedded_articles": embedded_articles,
                "pending_articles": pending_articles,
                "completion_rate": round(embedded_articles / total_articles * 100, 1) if total_articles > 0 else 0,
                "model_stats": model_stats
            }
    
    async def generate_embeddings_for_articles(self, 
                                             articles: List[Dict[str, Any]],
                                             batch_size: int = 10) -> int:
        """
        Generate embeddings for a list of articles and save to database.
        
        Args:
            articles: List of article dictionaries
            batch_size: Number of articles to process at once
            
        Returns:
            Number of articles successfully processed
        """
        if not articles:
            logger.warning("No articles provided for embedding generation")
            return 0
        
        # Load the embedding model
        await self.embedding_generator.load_model()
        
        processed_count = 0
        
        # Process articles in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            try:
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(articles)-1)//batch_size + 1} ({len(batch)} articles)")
                
                # Generate embeddings for batch
                embedded_batch = await self.embedding_generator.embed_articles(
                    batch,
                    content_field="content",
                    title_field="title",
                    combine_title_content=True
                )
                
                # Save embeddings to database
                await self._save_embeddings_to_db(embedded_batch)
                processed_count += len(embedded_batch)
                
                logger.info(f"Successfully processed {len(embedded_batch)} articles in batch")
                
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                continue
        
        logger.info(f"Completed embedding generation for {processed_count}/{len(articles)} articles")
        return processed_count
    
    async def _save_embeddings_to_db(self, articles: List[Dict[str, Any]]) -> None:
        """Save article embeddings to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for article in articles:
                embedding_json = json.dumps(article["embedding"])
                
                cursor.execute("""
                    UPDATE articles 
                    SET embedding = ?, embedding_model = ?, embedding_dim = ?
                    WHERE id = ?
                """, (
                    embedding_json,
                    article["embedding_model"],
                    article["embedding_dim"],
                    article["id"]
                ))
            
            conn.commit()
    
    async def process_all_articles(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Process all articles without embeddings.
        
        Args:
            batch_size: Number of articles to process at once
            
        Returns:
            Processing summary
        """
        # Set up database schema
        await self.setup_database()
        
        # Get initial statistics
        initial_stats = await self.get_embedding_statistics()
        logger.info(f"Initial state: {initial_stats}")
        
        if initial_stats["pending_articles"] == 0:
            logger.info("All articles already have embeddings!")
            return initial_stats
        
        # Get articles that need embeddings
        articles = await self.get_articles_without_embeddings()
        
        if not articles:
            logger.info("No articles found that need embeddings")
            return initial_stats
        
        # Process articles
        processed_count = await self.generate_embeddings_for_articles(articles, batch_size)
        
        # Get final statistics
        final_stats = await self.get_embedding_statistics()
        
        # Create summary
        summary = {
            "initial_stats": initial_stats,
            "final_stats": final_stats,
            "processed_articles": processed_count,
            "success_rate": round(processed_count / len(articles) * 100, 1) if articles else 0
        }
        
        logger.info(f"Processing complete: {summary}")
        return summary
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.embedding_generator.cleanup()


async def main():
    """Main function for command-line usage."""
    print("🚀 Article Embedding Management")
    print("=" * 50)
    
    manager = ArticleEmbeddingManager()
    
    try:
        # Setup database schema first
        print("🔧 Setting up database schema...")
        await manager.setup_database()
        
        # Check current status
        print("📊 Checking current embedding status...")
        stats = await manager.get_embedding_statistics()
        
        print(f"   Total articles: {stats['total_articles']}")
        print(f"   Embedded articles: {stats['embedded_articles']}")
        print(f"   Pending articles: {stats['pending_articles']}")
        print(f"   Completion rate: {stats['completion_rate']}%")
        
        if stats['model_stats']:
            print(f"   Models used: {stats['model_stats']}")
        
        if stats['pending_articles'] == 0:
            print("\n✅ All articles already have embeddings!")
            return
        
        # Process articles
        print(f"\n🔄 Processing {stats['pending_articles']} articles...")
        summary = await manager.process_all_articles(batch_size=5)
        
        print("\n✅ Processing complete!")
        print(f"   Processed: {summary['processed_articles']} articles")
        print(f"   Success rate: {summary['success_rate']}%")
        print(f"   Final completion rate: {summary['final_stats']['completion_rate']}%")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
