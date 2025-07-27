import pytest

@pytest.fixture
def sample_article():
    return {
        "title": "Sample Article",
        "content": "This is a sample article content.",
        "author": "Author Name"
    }

@pytest.fixture
def sample_news_service():
    return {
        "id": 1,
        "title": "Sample News",
        "description": "This is a sample news description.",
        "published_at": "2023-01-01T00:00:00Z"
    }