#!/usr/bin/env python3
"""Fresh test with no cache issues"""

import sys

# Add current directory to path for imports
sys.path.insert(0, '.')

# Import and check the actual method
from src.repositories.article_repository import ArticleRepository
import inspect

print("Checking ArticleRepository._row_to_article method...")
lines = inspect.getsourcelines(ArticleRepository._row_to_article)
print(f"Method has {len(lines[0])} lines")
print("First 10 lines:")
for i, line in enumerate(lines[0][:10]):
    print(f"  {i+1}: {line.rstrip()}")

# Check if it contains the key fields we expect
source_code = ''.join(lines[0])
has_author = 'author=row["author"]' in source_code
has_categories = 'categories=categories' in source_code  
has_metadata = 'metadata=metadata' in source_code

print("\nKey field assignments present:")
print(f"  author: {has_author}")
print(f"  categories: {has_categories}")
print(f"  metadata: {has_metadata}")

if not (has_author and has_categories and has_metadata):
    print("\n❌ FOUND THE BUG! The _row_to_article method is missing key field assignments!")
else:
    print("\n✅ Method looks correct")
