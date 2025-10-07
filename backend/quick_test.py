#!/usr/bin/env python3
"""
Quick Test Runner - No waiting, instant results!
===============================================
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_models():
    """Test core models directly"""
    try:
        from src.models.article import ArticleSummary, AISummary
        from datetime import datetime, timezone
        
        # Test ArticleSummary
        ArticleSummary(
            id=1, 
            title='Test', 
            summary='Test summary', 
            source='test.com',
            published_date=datetime.now(timezone.utc),
            url='http://test.com'
        )
        print("✓ ArticleSummary works")
        
        # Test AISummary
        AISummary(summary='AI generated summary')
        print("✓ AISummary works")
        
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_news_service():
    """Test NewsService initialization"""
    try:
        from src.services.news_service import NewsService
        service = NewsService()
        
        # Check required attributes
        assert hasattr(service, 'article_min_length'), "Missing article_min_length"
        assert hasattr(service, 'max_articles_per_feed'), "Missing max_articles_per_feed"
        print("✓ NewsService initialization works")
        return True
    except Exception as e:
        print(f"❌ NewsService error: {e}")
        return False

def test_health_routes():
    """Test health route models"""
    try:
        from src.models.api import HealthResponse, ComponentHealth
        
        # Test ComponentHealth with required name field
        ComponentHealth(name="database", status="healthy")
        print("✓ ComponentHealth works")
        
        # Test HealthResponse with components
        HealthResponse(
            status="healthy",
            components={"database": {"status": "healthy"}}
        )
        print("✓ HealthResponse works")
        return True
    except Exception as e:
        print(f"❌ Health routes error: {e}")
        return False

def main():
    """Run all quick tests"""
    print("🚀 Quick Test Runner - Instant Results!")
    print("=" * 50)
    
    tests = [
        ("Models", test_models),
        ("NewsService", test_news_service),
        ("Health Routes", test_health_routes),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All core components working!")
    else:
        print("⚠️  Some issues need fixing")
    
    return passed == total

if __name__ == "__main__":
    main()
