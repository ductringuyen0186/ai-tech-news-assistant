#!/usr/bin/env python3
"""Find the actual ArticleRepository file being imported"""

import sys
import os

# Add the backend directory to the path
backend_path = os.path.join(os.getcwd(), 'backend')
sys.path.insert(0, backend_path)

from src.repositories.article_repository import ArticleRepository
import inspect

print(f"ArticleRepository class file: {inspect.getfile(ArticleRepository)}")
print(f"ArticleRepository module: {inspect.getmodule(ArticleRepository)}")
print(f"ArticleRepository source file: {inspect.getsourcefile(ArticleRepository)}")

# Let's also check the create method
create_method = getattr(ArticleRepository, 'create')
print(f"Create method source lines:")
try:
    source_lines = inspect.getsourcelines(create_method)
    for i, line in enumerate(source_lines[0][:10]):  # First 10 lines
        print(f"  {source_lines[1] + i}: {line.rstrip()}")
except Exception as e:
    print(f"Error getting source: {e}")
