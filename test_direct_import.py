#!/usr/bin/env python3
"""Test the ArticleRepository directly without pytest cache issues"""

import sys
import os
import asyncio
import tempfile

# Add the backend directory to the path
backend_path = os.path.join(os.getcwd(), 'backend')
sys.path.insert(0, backend_path)

from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate

async def test_direct():
    print("Testing ArticleRepository directly...")
    
    # Create a temp database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        repo = ArticleRepository(db_path)
        
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
        print(f"Created ArticleCreate: author={article.author}")
        
        # This should trigger the RuntimeError if my changes are picked up
        result = await repo.create(article)
        print(f"ERROR: No RuntimeError thrown! Got result: {result}")
        
    except RuntimeError as e:
        print(f"SUCCESS: RuntimeError caught: {e}")
    except Exception as e:
        print(f"Other error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_direct())
