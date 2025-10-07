from datetime import datetime
import pytest

@pytest.fixture
def news_service_data():
    return {
        "title": "Breaking News",
        "content": "This is the content of the breaking news.",
        "published_at": datetime.now(),
        "author": "Author Name"
    }

def test_news_service_fixture(news_service_data):
    assert news_service_data["title"] == "Breaking News"
    assert news_service_data["author"] == "Author Name"
    assert "content" in news_service_data
    assert isinstance(news_service_data["published_at"], datetime)