#!/usr/bin/env python3
"""
Quick test to verify all imports work for the demo
"""

def test_imports():
    print("Testing imports...")
    
    try:
        # Test RSSFeedManager
        from ingestion.rss_feeds import RSSFeedManager
        print("✓ RSSFeedManager imported successfully")
    except ImportError as e:
        print(f"✗ RSSFeedManager import failed: {e}")
    
    try:
        # Test ContentParser
        from ingestion.content_parser import ContentParser
        print("✓ ContentParser imported successfully")
    except ImportError as e:
        print(f"✗ ContentParser import failed: {e}")
    
    try:
        # Test NewsService
        from src.services.news_service import NewsService
        print("✓ NewsService imported successfully")
    except ImportError as e:
        print(f"✗ NewsService import failed: {e}")
    
    try:
        # Test EmbeddingService
        from src.services.embedding_service import EmbeddingService
        print("✓ EmbeddingService imported successfully")
    except ImportError as e:
        print(f"✗ EmbeddingService import failed: {e}")
    
    try:
        # Test Article model
        from ingestion.rss_feeds import Article
        print("✓ Article model imported successfully")
    except ImportError as e:
        print(f"✗ Article model import failed: {e}")
    
    print("\nImport test completed!")

if __name__ == "__main__":
    test_imports()
