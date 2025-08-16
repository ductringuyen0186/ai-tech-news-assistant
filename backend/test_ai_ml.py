#!/usr/bin/env python3
"""
Quick test of core AI/ML functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

async def test_core_functionality():
    print("🧪 Testing core AI/ML functionality...")
    
    try:
        # Test RSSFeedManager
        print("\n📡 Testing RSS feed fetching...")
        from ingestion.rss_feeds import RSSFeedManager
        
        rss_manager = RSSFeedManager()
        test_articles = await rss_manager.fetch_articles(
            "https://www.theverge.com/rss/index.xml",
            limit=2
        )
        print(f"✅ Fetched {len(test_articles)} test articles")
        
        if test_articles:
            sample_article = test_articles[0]
            title = sample_article.get('title', 'Unknown title') if isinstance(sample_article, dict) else sample_article.title
            print(f"   Sample article: {title[:50]}...")
        
        # Test ContentParser
        print("\n🔍 Testing content parsing...")
        from ingestion.content_parser import ContentParser
        
        async with ContentParser() as parser:
            if test_articles:
                article_url = test_articles[0].get('url') if isinstance(test_articles[0], dict) else test_articles[0].url
                content, metadata = await parser.extract_content(article_url)
                if content:
                    print(f"✅ Extracted {len(content)} characters of content")
                    print(f"   Metadata: {list(metadata.keys())}")
                else:
                    print("⚠️ No content extracted")
            else:
                print("⚠️ No test articles to parse")
        
        # Test EmbeddingService
        print("\n🔮 Testing embedding generation...")
        from src.services.embedding_service import EmbeddingService
        from src.models.embedding import EmbeddingRequest
        
        embedding_service = EmbeddingService()
        await embedding_service.initialize()
        
        request = EmbeddingRequest(
            texts=["This is a test sentence for embedding generation."],
            batch_size=1
        )
        
        response = await embedding_service.generate_embeddings(request)
        print(f"✅ Generated embedding with dimension: {response.embedding_dim}")
        print(f"   Processing time: {response.processing_time:.2f}s")
        
        # Test NewsService
        print("\n📰 Testing news service...")
        from src.services.news_service import NewsService
        
        news_service = NewsService()
        await news_service.initialize()
        
        # Add a test source
        result = await news_service.add_source(
            name="Test Source",
            url="https://www.theverge.com",
            rss_url="https://www.theverge.com/rss/index.xml",
            description="Test RSS source"
        )
        print(f"✅ Added test source: {result['status']}")
        
        # Test health check
        health = await news_service.health_check()
        print(f"   Service health: {health['status']}")
        
        await news_service.cleanup()
        
        print("\n🎯 All core tests completed successfully!")
        print("   The AI/ML features are ready for demonstration!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_core_functionality())
    if success:
        print("\n✅ AI/ML demo is ready to run!")
    else:
        print("\n❌ Some issues need to be resolved before running the demo")
        sys.exit(1)
