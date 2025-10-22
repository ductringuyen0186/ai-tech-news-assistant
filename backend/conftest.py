import pytest
import sqlite3
from datetime import datetime
from fastapi.testclient import TestClient
from pathlib import Path

# Import app and fixtures
from src.main import app
from src.repositories.article_repository import ArticleRepository
from tests.fixtures.article_fixtures import get_article_fixtures


@pytest.fixture
def sample_article():
    return {
        "title": "Sample Article",
        "content": "This is a sample article content.",
        "author": "Author Name"
    }

@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        "title": "AI Breakthrough in NLP",
        "content": "Researchers have discovered a new approach to natural language processing.",
        "author": "Jane Researcher",
        "source": "techcrunch.com",
        "url": "https://techcrunch.com/ai-nlp",
        "published_at": datetime.now(),
        "categories": ["AI", "NLP"],
        "summary": "A new NLP approach"
    }

@pytest.fixture
def sample_news_service():
    return {
        "id": 1,
        "title": "Sample News",
        "description": "This is a sample news description.",
        "published_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database file for testing."""
    db_file = tmp_path / "test_articles.db"
    return str(db_file)


@pytest.fixture
def test_db(test_db_path):
    """Create and initialize test database."""
    repo = ArticleRepository(test_db_path)
    
    # Insert sample articles
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    articles = get_article_fixtures()
    for article in articles:
        cursor.execute("""
            INSERT INTO articles (title, content, author, source, url, published_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get("title"),
            article.get("content", ""),
            article.get("author", ""),
            article.get("source", "test"),
            article.get("url", f"https://test.com/{article.get('id')}"),
            article.get("published_date", datetime.now().isoformat()),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
    
    yield repo
    
    # Cleanup
    Path(test_db_path).unlink(missing_ok=True)


@pytest.fixture
def client():
    """Create test client for API routes."""
    return TestClient(app)