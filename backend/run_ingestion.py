"""
Quick Ingestion Script
=====================
Fetch articles from RSS feeds and populate the database.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.rss_feeds import ingest_tech_news


async def main():
    """Run article ingestion."""
    print("🚀 Starting article ingestion from RSS feeds...")
    print("📰 This will fetch articles from Hacker News, TechCrunch, and other sources")
    print()
    
    try:
        # Ingest without full content parsing (faster)
        result = await ingest_tech_news(parse_content=False)
        
        print("\n✅ Ingestion Complete!")
        print(f"   Total articles processed: {result.get('total_articles', 0)}")
        print(f"   New articles added: {result.get('new_articles', 0)}")
        print(f"   Duplicates skipped: {result.get('duplicates', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        print()
        print("🎉 You can now test the search functionality!")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
