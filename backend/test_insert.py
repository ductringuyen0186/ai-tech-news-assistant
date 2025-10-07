"""Test direct SQL insert"""
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('data/articles.db')

# Test insert
article_data = {
    'id': 'test123',
    'title': 'Test Article',
    'url': 'https://example.com/test',
    'content': '',
    'description': 'Test description',
    'author': 'Test Author',
    'published_date': '2025-10-07T12:00:00',
    'source': 'Test',
    'tags': json.dumps(['test']),
}

try:
    cursor = conn.execute("""
        INSERT INTO articles 
        (id, title, url, content, description, author, published_date, source, 
         tags, content_length, content_parsed_at, 
         content_parser_method, content_metadata, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        article_data['id'],
        article_data['title'],
        article_data['url'],
        article_data['content'],
        article_data['description'],
        article_data['author'],
        article_data['published_date'],
        article_data['source'],
        article_data['tags'],
        None,  # content_length
        None,  # content_parsed_at
        None,  # content_parser_method
        None   # content_metadata
    ))
    
    print(f"Rowcount: {cursor.rowcount}")
    conn.commit()
    
    # Check
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"Articles in DB: {count}")
    
    if count > 0:
        row = conn.execute("SELECT id, title FROM articles LIMIT 1").fetchone()
        print(f"Sample: {row}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()
