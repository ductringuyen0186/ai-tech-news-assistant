import asyncio
import tempfile
import os
import sqlite3
import json
import sys
sys.path.append('backend')
from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, Article

def test_manual_row_to_article():
    """Test exactly what _row_to_article does"""
    
    # Simulate a sqlite3.Row object
    class MockRow:
        def __init__(self, data):
            self._data = data
        
        def __getitem__(self, key):
            return self._data[key]
        
        def keys(self):
            return self._data.keys()
    
    # Create row with the exact data we saw in debug
    row_data = {
        'id': 1,
        'title': 'Test Article Title',
        'url': 'https://example.com/test-article',
        'content': 'This is test article content',
        'summary': None,
        'author': 'Test Author',
        'published_at': None,
        'created_at': '2025-07-25 02:22:39',
        'updated_at': '2025-07-25 02:22:39',
        'source': 'test-source.com',
        'categories': '["technology", "ai"]',  # JSON string
        'metadata': '{"test": true}',  # JSON string
        'is_archived': 0,
        'view_count': 0,
        'embedding_generated': 0
    }
    
    row = MockRow(row_data)
    
    print("Testing manual _row_to_article logic:")
    
    # Parse JSON fields safely (copied from _row_to_article)
    categories = None
    if row["categories"]:
        try:
            categories = json.loads(row["categories"])
            print(f"Parsed categories: {categories}")
        except (json.JSONDecodeError, TypeError):
            categories = None
            print("Failed to parse categories")
    
    metadata = None
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
            print(f"Parsed metadata: {metadata}")
        except (json.JSONDecodeError, TypeError):
            metadata = None
            print("Failed to parse metadata")
    
    # Create Article (copied from _row_to_article)
    print("\nTrying to create Article with these exact parameters:")
    article_kwargs = {
        'id': row["id"],
        'title': row["title"],
        'url': row["url"],
        'content': row["content"],
        'summary': row["summary"],
        'source': row["source"],
        'author': row["author"],
        'published_at': row["published_at"],
        'categories': categories,
        'metadata': metadata,
        'created_at': row["created_at"],
        'updated_at': row["updated_at"],
        'is_archived': bool(row["is_archived"]),
        'view_count': row["view_count"] or 0,
        'embedding_generated': bool(row["embedding_generated"]),
        'published_date': row["published_at"]
    }
    
    for key, value in article_kwargs.items():
        print(f"  {key}: {repr(value)} ({type(value)})")
    
    try:
        article = Article(**article_kwargs)
        print(f"\nSuccess! Created article:")
        print(f"  author: {article.author}")
        print(f"  categories: {article.categories}")
        print(f"  metadata: {article.metadata}")
    except Exception as e:
        print(f"\nError creating Article: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manual_row_to_article()
