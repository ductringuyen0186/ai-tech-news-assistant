#!/usr/bin/env python3
"""
Quick test of IngestionService functionality
"""
from src.services.ingestion_service import IngestionService, IngestionStatus
from src.database import get_db

def test_ingestion():
    """Test ingestion system end-to-end."""
    print("🚀 Testing IngestionService...")
    print()
    
    # Initialize database tables
    from src.database import init_db
    print("📦 Initializing database tables...")
    init_db()
    print("✅ Database initialized")
    print()
    
    # Get database session
    db = next(get_db())
    
    # Create service
    service = IngestionService(db, batch_size=5)
    
    # Test with just 1 feed for quick testing
    custom_feeds = [
        {
            "name": "HackerNews",
            "url": "https://news.ycombinator.com/rss",
            "category": "AI"
        }
    ]
    
    print(f"📰 Ingesting from {len(custom_feeds)} feed(s)...")
    print(f"Feed: {custom_feeds[0]['name']} -> {custom_feeds[0]['url']}")
    print()
    
    try:
        # Run ingestion
        result = service.ingest_all(custom_feeds)
        
        # Display results
        print("✅ INGESTION COMPLETE")
        print()
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Total feeds: {result.total_feeds}")
        print(f"Articles found: {result.total_articles_found}")
        print(f"Articles saved: {result.total_articles_saved}")
        print(f"Duplicates skipped: {result.duplicates_skipped}")
        print(f"Errors: {result.errors_encountered}")
        print(f"Success rate: {result.success_rate:.1f}%")
        
        if result.error_details:
            print()
            print("⚠️  Errors encountered:")
            for error in result.error_details:
                print(f"  - {error}")
        
        # Get stats
        print()
        print("📊 Database Statistics:")
        stats = service.get_stats()
        print(f"Total articles in DB: {stats['total_articles']}")
        print(f"Total sources: {stats['total_sources']}")
        print(f"Total categories: {stats['total_categories']}")
        
        return result.status == IngestionStatus.COMPLETED or result.status == IngestionStatus.PARTIAL
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        service.close()
        db.close()

if __name__ == "__main__":
    success = test_ingestion()
    exit(0 if success else 1)
