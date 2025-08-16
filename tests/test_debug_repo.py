import asyncio
import tempfile
import os
import sqlite3
import json
import sys
sys.path.append('backend')
from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, Article

class DebugArticleRepository(ArticleRepository):
    def _row_to_article(self, row):
        print(f"\n=== DEBUG _row_to_article ===")
        print(f"Row type: {type(row)}")
        if not row:
            print("Row is falsy, returning None")
            return None
        
        print(f"Row data access test:")
        try:
            print(f"  author: {repr(row['author'])}")
            print(f"  categories: {repr(row['categories'])}")
            print(f"  metadata: {repr(row['metadata'])}")
        except Exception as e:
            print(f"  Error accessing row data: {e}")
        
        # Parse JSON fields safely
        categories = None
        if row["categories"]:
            try:
                categories = json.loads(row["categories"])
                print(f"Successfully parsed categories: {categories}")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to parse categories: {e}")
                categories = None
        else:
            print("Categories is falsy")
        
        metadata = None
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
                print(f"Successfully parsed metadata: {metadata}")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to parse metadata: {e}")
                metadata = None
        else:
            print("Metadata is falsy")
        
        print(f"Creating Article with:")
        print(f"  author: {repr(row['author'])}")
        print(f"  categories: {repr(categories)}")
        print(f"  metadata: {repr(metadata)}")
        
        try:
            article = Article(
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
            print(f"Article created successfully!")
            print(f"  Result author: {repr(article.author)}")
            print(f"  Result categories: {repr(article.categories)}")
            print(f"  Result metadata: {repr(article.metadata)}")
            return article
        except Exception as e:
            print(f"Error creating Article: {e}")
            import traceback
            traceback.print_exc()
            return None

async def test_debug_repo():
    """Test with debug repository"""
    
    # Create a temp database and actual data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        repo = DebugArticleRepository(db_path)
        
        # Test data
        sample_data = {
            'title': 'Test Article Title',
            'url': 'https://example.com/test-article',
            'content': 'This is test article content',
            'author': 'Test Author',
            'source': 'test-source.com',
            'categories': ['technology', 'ai'],
            'metadata': {'test': True}
        }
        
        article = ArticleCreate(**sample_data)
        
        # Create the article
        result = await repo.create(article)
        print(f"Created article with ID: {result.id}")
        
        # Now try to get it back
        retrieved = await repo.get_by_id(result.id)
        print(f"\nRetrieved article: {retrieved}")
        
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_debug_repo())
