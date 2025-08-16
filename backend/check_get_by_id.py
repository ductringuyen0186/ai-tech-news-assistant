#!/usr/bin/env python3
"""Check get_by_id method"""

import sys
import inspect

sys.path.insert(0, '.')

# Force remove from cache
for module in list(sys.modules.keys()):
    if 'src.repositories' in module:
        del sys.modules[module]

from src.repositories.article_repository import ArticleRepository

# Check the get_by_id method
method = ArticleRepository.get_by_id
lines = inspect.getsourcelines(method)
source = ''.join(lines[0])

print("get_by_id method:")
for i, line in enumerate(lines[0]):
    print(f"  {i+1}: {line.rstrip()}")

# Check if it filters archived articles
has_archived_filter = "is_archived = FALSE" in source
print(f"\nFilters archived articles: {has_archived_filter}")

if not has_archived_filter:
    print("❌ Method doesn't filter archived articles!")
else:
    print("✅ Method correctly filters archived articles")
