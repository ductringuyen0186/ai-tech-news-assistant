import asyncio
import tempfile
import os
import sqlite3
import json
import sys
sys.path.append('backend')
from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, Article

async def test_article_creation():
    # Test creating Article directly with the exact data from the database
    raw_data = {
        'id': 1,
        'title': 'Test Article Title',
        'url': 'https://example.com/test-article',
        'content': 'This is test article content',
        'summary': None,
        'source': 'test-source.com',
        'author': 'Test Author',
        'published_at': None,
        'categories': ['technology', 'ai'],  # Already parsed
        'metadata': {'test': True},  # Already parsed
        'created_at': '2025-07-25 02:22:39',
        'updated_at': '2025-07-25 02:22:39',
        'is_archived': False,
        'view_count': 0,
        'embedding_generated': False,
        'published_date': None
    }
    
    print('Testing Article creation with all fields:')
    try:
        article = Article(**raw_data)
        print(f'Success! author: {article.author}')
        print(f'categories: {article.categories}')
        print(f'metadata: {article.metadata}')
        return article
    except Exception as e:
        print(f'Error creating Article: {e}')
        import traceback
        traceback.print_exc()
        return None

    print('\nTesting Article creation with minimal fields:')
    minimal_data = {
        'id': 1,
        'title': 'Test Article Title',
        'url': 'https://example.com/test-article',
        'content': 'This is test article content',
        'source': 'test-source.com',
        'author': 'Test Author',
        'categories': ['technology', 'ai'],
        'metadata': {'test': True}
    }
    try:
        article = Article(**minimal_data)
        print(f'Success! author: {article.author}')
        print(f'categories: {article.categories}')
        print(f'metadata: {article.metadata}')
    except Exception as e:
        print(f'Error creating Article: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_article_creation())
