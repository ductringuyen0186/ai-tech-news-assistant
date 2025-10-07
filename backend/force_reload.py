#!/usr/bin/env python3
"""Force reload and check"""

import sys

# Add current directory to path
sys.path.insert(0, '.')

# Force remove from cache if exists
if 'src.repositories.article_repository' in sys.modules:
    del sys.modules['src.repositories.article_repository']
if 'src.repositories' in sys.modules:
    del sys.modules['src.repositories']

# Now import fresh
from src.repositories.article_repository import ArticleRepository
import inspect

print("After forced reload - Checking method...")
lines = inspect.getsourcelines(ArticleRepository._row_to_article)
print(f"Method has {len(lines[0])} lines")

# Check if it contains the key fields we expect
source_code = ''.join(lines[0])
has_author = 'author=row["author"]' in source_code
has_categories = 'categories=categories' in source_code  
has_metadata = 'metadata=metadata' in source_code

print("Key field assignments present:")
print(f"  author: {has_author}")
print(f"  categories: {has_categories}")
print(f"  metadata: {has_metadata}")

if not (has_author and has_categories and has_metadata):
    print("\n❌ Still using old cached version!")
    print("First 15 lines of actual method:")
    for i, line in enumerate(lines[0][:15]):
        print(f"  {i+1}: {line.rstrip()}")
else:
    print("\n✅ Successfully loaded correct version!")
