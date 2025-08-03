import asyncio
import tempfile
import os
import sqlite3
import json
import sys
sys.path.append('backend')
from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, Article

def test_repo_method():
    """Test the actual repository _row_to_article method"""
    
    # Create a temporary repository
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        repo = ArticleRepository(db_path)
        
        # Simulate a sqlite3.Row object with exact data
        class MockRow:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data[key]
            
            def keys(self):
                return self._data.keys()
        
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
            'categories': '["technology", "ai"]',
            'metadata': '{"test": true}',
            'is_archived': 0,
            'view_count': 0,
            'embedding_generated': 0
        }
        
        row = MockRow(row_data)
        
        print("Testing repository _row_to_article method:")
        result = repo._row_to_article(row)
        
        if result:
            print(f"Success! author: {result.author}")
            print(f"categories: {result.categories}")
            print(f"metadata: {result.metadata}")
        else:
            print("ERROR: _row_to_article returned None!")
            
        # Let's also test with None row
        print("\nTesting with None row:")
        result2 = repo._row_to_article(None)
        print(f"Result for None: {result2}")
        
        # Let's test with empty row
        print("\nTesting with empty categories/metadata:")
        row_data_empty = row_data.copy()
        row_data_empty['categories'] = None
        row_data_empty['metadata'] = None
        row_empty = MockRow(row_data_empty)
        result3 = repo._row_to_article(row_empty)
        if result3:
            print(f"Success with empty! author: {result3.author}")
            print(f"categories: {result3.categories}")
            print(f"metadata: {result3.metadata}")
        else:
            print("ERROR: _row_to_article returned None for empty categories/metadata!")
    
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass

if __name__ == "__main__":
    test_repo_method()
