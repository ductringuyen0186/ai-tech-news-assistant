#!/usr/bin/env python3
"""
Test Content Parsing for AI Tech News Assistant
==============================================

This script tests the content parsing functionality by:
1. Fetching a few RSS articles
2. Parsing their full content
3. Displaying the results

Usage:
    python test_content_parser.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from ingestion.content_parser import ContentParser
from ingestion.rss_feeds import RSSFeedIngester
from utils.logger import get_logger

logger = get_logger(__name__)


async def test_content_parser():
    """Test the content parser with sample URLs."""
    
    print("🔍 Testing Content Parser")
    print("=" * 50)
    
    # Test URLs (well-known tech news sites)
    test_urls = [
        "https://techcrunch.com/2023/01/01/openai-chatgpt/",  # Example URL
        "https://arstechnica.com/tech-policy/",  # Example URL
    ]
    
    async with ContentParser() as parser:
        for url in test_urls:
            print(f"\n📄 Testing URL: {url}")
            print("-" * 30)
            
            try:
                content, metadata = await parser.extract_content(url)
                
                if content:
                    print("✅ Success!")
                    print(f"   Method: {metadata.get('method', 'unknown')}")
                    print(f"   Content length: {len(content)} characters")
                    print(f"   Title: {metadata.get('title', 'N/A')}")
                    print(f"   Preview: {content[:200]}...")
                else:
                    print("❌ Failed to extract content")
                    print(f"   Error: {metadata.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")


async def test_rss_with_content_parsing():
    """Test RSS ingestion with content parsing."""
    
    print("\n\n🔗 Testing RSS Ingestion with Content Parsing")
    print("=" * 50)
    
    async with RSSFeedIngester() as ingester:
        # Test with a single, reliable source
        test_source = {
            "name": "O'Reilly Radar",
            "url": "https://feeds.feedburner.com/oreilly/radar"
        }
        
        print(f"📡 Fetching from: {test_source['name']}")
        
        # Fetch RSS articles
        articles = await ingester.fetch_feed(test_source['url'], test_source['name'])
        
        if articles:
            print(f"✅ Found {len(articles)} articles")
            
            # Test content parsing on first article
            if articles:
                article = articles[0]
                print(f"\n📄 Testing content parsing for: {article.title}")
                print(f"   URL: {article.url}")
                
                async with ContentParser() as parser:
                    content, metadata = await parser.extract_content(str(article.url))
                    
                    if content:
                        print("✅ Content parsing successful!")
                        print(f"   Method: {metadata.get('method', 'unknown')}")
                        print(f"   Content length: {len(content)} characters")
                        print(f"   Preview: {content[:300]}...")
                    else:
                        print("❌ Content parsing failed")
                        print(f"   Error: {metadata.get('error', 'Unknown error')}")
        else:
            print("❌ No articles found")


async def test_database_operations():
    """Test storing articles with content parsing."""
    
    print("\n\n💾 Testing Database Operations")
    print("=" * 50)
    
    async with RSSFeedIngester() as ingester:
        # Ingest with content parsing (limited to avoid overwhelming servers)
        print("📥 Ingesting RSS feeds with content parsing...")
        
        # Modify the default sources to limit testing
        original_sources = ingester.DEFAULT_SOURCES
        ingester.DEFAULT_SOURCES = [ingester.DEFAULT_SOURCES[0]]  # Only use first source
        
        try:
            summary = await ingester.ingest_all_feeds(parse_content=True)
            print("✅ Ingestion completed!")
            print(f"   Total fetched: {summary['total_fetched']}")
            print(f"   Total stored: {summary['total_stored']}")
            print(f"   Content parsed: {summary['content_parsed']}")
            
            # Show article statistics
            articles = ingester.get_articles(limit=5)
            print("\n📊 Sample articles:")
            for i, article in enumerate(articles, 1):
                content_len = len(article.get('content', '')) if article.get('content') else 0
                print(f"   {i}. {article['title'][:50]}...")
                print(f"      Content length: {content_len} characters")
                
        finally:
            # Restore original sources
            ingester.DEFAULT_SOURCES = original_sources


async def main():
    """Run all tests."""
    print("🧪 AI Tech News Assistant - Content Parser Tests")
    print("=" * 60)
    
    try:
        # Test 1: Direct content parser testing
        await test_content_parser()
        
        # Test 2: RSS ingestion with content parsing
        await test_rss_with_content_parsing()
        
        # Test 3: Database operations
        await test_database_operations()
        
        print("\n\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Test error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
