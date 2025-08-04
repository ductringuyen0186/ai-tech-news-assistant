import sys
sys.path.append('backend')
from src.models.article import Article
import json

# Test data that matches the test case
test_data = {
    'id': 1,
    'title': 'Test Article Title',
    'url': 'https://example.com/test-article',
    'content': 'This is test article content with enough text to be meaningful for testing purposes.',
    'summary': None,
    'source': 'test-source.com',
    'author': 'Test Author',
    'published_at': None,
    'categories': ['technology', 'ai'],
    'metadata': {'test': True},
    'created_at': None,
    'updated_at': None,
    'is_archived': False,
    'view_count': 0,
    'embedding_generated': False,
    'published_date': None
}

print("Testing Article creation with test data:")
try:
    article = Article(**test_data)
    print(f"Success!")
    print(f"  author: {repr(article.author)}")
    print(f"  categories: {repr(article.categories)}")
    print(f"  metadata: {repr(article.metadata)}")
    
    # Also test the serialization
    print(f"\nSerialized:")
    print(f"  {article}")
    
    # Test creating with string dates (like from database)
    print(f"\nTesting with string dates:")
    test_data_with_dates = test_data.copy()
    test_data_with_dates['created_at'] = '2025-07-25 02:22:39'
    test_data_with_dates['updated_at'] = '2025-07-25 02:22:39'
    
    article2 = Article(**test_data_with_dates)
    print(f"Success with string dates!")
    print(f"  author: {repr(article2.author)}")
    print(f"  categories: {repr(article2.categories)}")
    print(f"  metadata: {repr(article2.metadata)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
