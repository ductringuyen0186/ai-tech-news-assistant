"""
Setup Script for Refactored Codebase
===================================

This script helps transition from the old monolithic structure
to the new refactored architecture.
"""

import os
import shutil
import sys
from pathlib import Path


def backup_old_files():
    """Backup original files before transition."""
    backup_dir = Path("backup_old_structure")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "api/routes.py",
        "utils/config.py", 
        "utils/logger.py",
        "vectorstore/embeddings.py"
    ]
    
    print("📦 Backing up old files...")
    for file_path in files_to_backup:
        if Path(file_path).exists():
            dest = backup_dir / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
            print(f"  ✅ Backed up {file_path}")


def update_requirements():
    """Update requirements.txt with any new dependencies."""
    requirements_content = """
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.4.2
pydantic-settings==2.0.3

# Database
sqlite3  # Built into Python

# HTTP client
httpx==0.25.0

# RSS parsing
feedparser==6.0.10

# Content parsing
beautifulsoup4==4.12.2
lxml==4.9.3

# AI/ML libraries (optional)
sentence-transformers==2.2.2
torch>=2.0.0
numpy>=1.24.0

# Development dependencies
pytest==7.4.0
pytest-asyncio==0.21.1
pytest-mock==3.11.1
black==23.7.0
flake8==6.0.0

# Logging
structlog==23.1.0
""".strip()
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    print("📝 Updated requirements.txt")


def create_migration_guide():
    """Create a migration guide documenting the changes."""
    guide_content = """
# Migration Guide: Refactored Codebase

## Overview
The codebase has been refactored from a monolithic structure to a clean, layered architecture.

## Key Changes

### Directory Structure
```
OLD:
backend/
├── api/routes.py (581 lines)
├── utils/config.py
├── utils/logger.py
├── vectorstore/embeddings.py (500+ lines)
└── ingestion/

NEW:
backend/
├── src/
│   ├── api/routes/           # Split by domain
│   │   ├── health.py
│   │   ├── news.py
│   │   ├── summarization.py
│   │   ├── embeddings.py
│   │   └── search.py
│   ├── core/                 # Core functionality
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   ├── services/             # Business logic
│   │   ├── news_service.py
│   │   ├── summarization_service.py
│   │   └── embedding_service.py
│   ├── repositories/         # Data access
│   │   ├── article_repository.py
│   │   └── embedding_repository.py
│   ├── models/              # Data models
│   │   ├── article.py
│   │   ├── embedding.py
│   │   ├── database.py
│   │   └── api.py
│   └── main.py              # Application entry point
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
└── scripts/               # Utility scripts
```

### Import Changes
```python
# OLD
from api.routes import router
from utils.config import get_settings
from utils.logger import get_logger

# NEW
from src.api.routes import api_router, root_router
from src.core.config import settings
from src.core.logging import setup_logging
```

### Running the Application
```bash
# OLD
cd backend
python -m uvicorn api.main:app --reload

# NEW
cd backend
python -m uvicorn src.main:app --reload
```

### Benefits
1. ✅ **Maintainable**: No file exceeds 350 lines
2. ✅ **Testable**: Comprehensive test coverage
3. ✅ **Scalable**: Clear separation of concerns
4. ✅ **Professional**: Industry-standard structure
5. ✅ **Type-safe**: Full Pydantic model coverage

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/e2e/           # End-to-end tests
```

### Configuration
All configuration is now centralized in `src/core/config.py` with proper environment variable support.

### Logging
Structured logging is set up in `src/core/logging.py` with proper log levels and formatting.

### Error Handling
Custom exceptions are defined in `src/core/exceptions.py` for better error categorization.
"""
    
    with open("MIGRATION_GUIDE.md", "w") as f:
        f.write(guide_content)
    
    print("📚 Created MIGRATION_GUIDE.md")


def main():
    """Main setup function."""
    print("🔧 Setting up refactored AI Tech News Assistant")
    print("=" * 50)
    
    # Change to backend directory if not already there
    if not Path("src").exists():
        if Path("backend").exists():
            os.chdir("backend")
        else:
            print("❌ Error: Cannot find backend directory")
            sys.exit(1)
    
    # Backup old files
    backup_old_files()
    
    # Update requirements
    update_requirements()
    
    # Create migration guide
    create_migration_guide()
    
    print("\n✨ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run tests: pytest tests/")
    print("3. Start application: python -m uvicorn src.main:app --reload")
    print("4. Check API docs: http://localhost:8000/docs")
    print("\nRefer to MIGRATION_GUIDE.md for detailed information.")


if __name__ == "__main__":
    main()
