"""
Debug Ingestion Script - Check what's happening
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ingestion.rss_feeds import RSSFeedIngester


async def main():
    """Run debug ingestion."""
    print("🔍 Debug Mode: Fetching a single feed")
    
    ingester = RSSFeedIngester()
    
    # Fetch just TechCrunch
    articles = await ingester.fetch_feed(
        "https://techcrunch.com/feed/",
        "TechCrunch"
    )
    
    print(f"\n📰 Fetched {len(articles)} articles")
    
    if articles:
        article = articles[0]
        print("\n📝 First Article:")
        print(f"   ID: {article.id}")
        print(f"   Title: {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Published: {article.published_date}")
        print(f"   Source: {article.source}")
        print(f"   Description: {article.description[:100]}..." if article.description else "None")
        
        # Try to store it
        print("\n💾 Attempting to store articles...")
        stored = await ingester.store_articles(articles[:1], parse_content=False)
        print(f"   Stored: {stored} articles")
        
        # Check database
        import sqlite3
        conn = sqlite3.connect('data/articles.db')
        count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"   Database now has: {count} articles")
        
        if count > 0:
            row = conn.execute("SELECT id, title FROM articles LIMIT 1").fetchone()
            print(f"   Sample: {row}")
        conn.close()
    
    await ingester.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
