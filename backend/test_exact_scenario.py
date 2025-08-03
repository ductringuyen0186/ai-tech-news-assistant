#!/usr/bin/env python3
"""Replicate the exact test scenario to isolate the issue"""

import sys
import os
import asyncio
import tempfile

# Add the backend directory to the path
backend_path = os.path.join(os.getcwd())
sys.path.insert(0, backend_path)

from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate
import importlib

# Force reload the modules to clear any cache
import src.repositories.article_repository
import src.models.article
importlib.reload(src.repositories.article_repository)
importlib.reload(src.models.article)

from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate

async def test_exact_scenario():
    print("Testing exact test scenario...")
    
    # Create a temp database exactly like the fixture
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        repo = ArticleRepository(db_path=db_path)
        
        # Use the exact sample data from the test fixture
        sample_article_data = {
            "title": "Test Article Title",
            "url": "https://example.com/test-article",
            "content": "This is test article content with enough text to be meaningful for testing purposes.",
            "author": "Test Author",
            "source": "test-source.com",
            "categories": ["technology", "ai"],
            "metadata": {"test": True}
        }
        
        # Create ArticleCreate exactly like the test
        article_data = ArticleCreate(**sample_article_data)
        print(f"ArticleCreate fields:")
        print(f"  title: {article_data.title}")
        print(f"  author: {article_data.author}")
        print(f"  categories: {article_data.categories}")
        print(f"  metadata: {article_data.metadata}")
        
        # Call create exactly like the test
        result = await repo.create(article_data)
        
        print(f"\nResult fields:")
        print(f"  id: {result.id}")
        print(f"  title: {result.title}")
        print(f"  author: {result.author}")
        print(f"  categories: {result.categories}")
        print(f"  metadata: {result.metadata}")
        
        # Check the assertions that are failing
        print(f"\nAssertion checks:")
        print(f"  result.id is not None: {result.id is not None}")
        print(f"  result.title == sample_data['title']: {result.title == sample_article_data['title']}")
        print(f"  result.author == sample_data['author']: {result.author == sample_article_data['author']}")
        
        if result.author != sample_article_data["author"]:
            print(f"  FAILURE: Expected '{sample_article_data['author']}', got '{result.author}'")
        else:
            print(f"  SUCCESS: Author field matches!")
        
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(test_exact_scenario())
