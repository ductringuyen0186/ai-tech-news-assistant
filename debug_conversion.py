import asyncio
import tempfile
import os
import sqlite3
import json
import sys
sys.path.append('backend')
from src.repositories.article_repository import ArticleRepository
from src.models.article import ArticleCreate, Article

async def debug_conversion():
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
        
        # Create the article
        result = await repo.create(article)
        
        # Now get the raw row and manually test the conversion
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            raw_row = conn.execute('SELECT * FROM articles WHERE id = ?', (result.id,)).fetchone()
            
            print('Raw row data:')
            print(f'  author: {repr(raw_row["author"])}')
            print(f'  categories: {repr(raw_row["categories"])}')
            print(f'  metadata: {repr(raw_row["metadata"])}')
            
            # Test manual conversion
            categories = None
            if raw_row['categories']:
                try:
                    categories = json.loads(raw_row['categories'])
                    print(f'  Parsed categories: {categories}')
                except Exception as e:
                    print(f'  Categories parse error: {e}')
            
            metadata = None
            if raw_row['metadata']:
                try:
                    metadata = json.loads(raw_row['metadata'])
                    print(f'  Parsed metadata: {metadata}')
                except Exception as e:
                    print(f'  Metadata parse error: {e}')
            
            # Test creating Article manually
            print('\nTesting Article creation:')
            try:
                manual_article = Article(
                    id=raw_row['id'],
                    title=raw_row['title'],
                    url=raw_row['url'],
                    content=raw_row['content'],
                    summary=raw_row['summary'],
                    source=raw_row['source'],
                    author=raw_row['author'],
                    published_at=raw_row['published_at'],
                    categories=categories,
                    metadata=metadata,
                    created_at=raw_row['created_at'],
                    updated_at=raw_row['updated_at'],
                    is_archived=bool(raw_row['is_archived']),
                    view_count=raw_row['view_count'] or 0,
                    embedding_generated=bool(raw_row['embedding_generated']),
                    published_date=raw_row['published_at']
                )
                print(f'  Success! author: {manual_article.author}')
                print(f'  categories: {manual_article.categories}')
                print(f'  metadata: {manual_article.metadata}')
                
                # Now test the repo method
                print('\nTesting repo _row_to_article method:')
                
                # Let's debug the method step by step
                print(f'Raw row type: {type(raw_row)}')
                print(f'Raw row keys: {list(raw_row.keys())}')
                
                # Test accessing each field individually
                for key in raw_row.keys():
                    print(f'  {key}: {repr(raw_row[key])} (type: {type(raw_row[key])})')
                
                repo_article = repo._row_to_article(raw_row)
                print(f'\nResult: {repo_article}')
                if repo_article:
                    print(f'  author: {repo_article.author}')
                    print(f'  categories: {repo_article.categories}')
                    print(f'  metadata: {repo_article.metadata}')
                else:
                    print('  ERROR: _row_to_article returned None!')
                    
            except Exception as e:
                print(f'  Manual Article creation error: {e}')
        
    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(debug_conversion())
