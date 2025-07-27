import pytest
from backend.services.news_service import NewsService
from backend.tests.fixtures.news_service_fixtures import valid_news_data

def test_news_service_get_news():
    service = NewsService()
    news = service.get_news()
    assert news is not None
    assert isinstance(news, list)

def test_news_service_article_count():
    service = NewsService()
    articles = service.get_articles()
    assert len(articles) > 0

def test_news_service_article_content():
    service = NewsService()
    article = service.get_article(valid_news_data['article_id'])
    assert article['title'] == valid_news_data['expected_title']
    assert article['content'] == valid_news_data['expected_content']