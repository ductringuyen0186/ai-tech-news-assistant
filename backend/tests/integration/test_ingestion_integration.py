"""
Integration test for the ingestion system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime
from src.services.ingestion_service import IngestionService, IngestionStatus, IngestionResult
from src.database.base import create_database_engine, create_session_factory, Base
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize database for testing
engine = create_database_engine()
Base.metadata.create_all(bind=engine)
session_factory = create_session_factory()


def test_ingestion_service():
    """Test the complete ingestion pipeline"""
    
    print("\n" + "="*60)
    print("INGESTION SERVICE TEST")
    print("="*60)
    
    # Create session
    Session = session_factory()
    
    try:
        # Initialize service
        print("\n1. Initializing IngestionService...")
        service = IngestionService(Session)
        print("   ✅ Service initialized")
        
        # Check default feeds
        print("\n2. Checking default RSS feeds...")
        print(f"   Total feeds configured: {len(service.DEFAULT_FEEDS)}")
        for feed in service.DEFAULT_FEEDS:
            print(f"     - {feed['name']} ({feed['category']})")
        print("   ✅ Feeds configured")
        
        # Run ingestion (with timeout)
        print("\n3. Running ingestion (this may take 2-5 minutes)...")
        print("   Fetching RSS feeds...")
        result = service.ingest_all()
        
        # Display results
        print("\n4. INGESTION RESULTS")
        print("   " + "-"*50)
        print(f"   Status: {result.status.value}")
        print(f"   Duration: {result.duration_seconds:.1f} seconds")
        print(f"   Total feeds: {result.total_feeds}")
        print(f"   Articles found: {result.total_articles_found}")
        print(f"   Articles saved: {result.total_articles_saved}")
        print(f"   Duplicates skipped: {result.duplicates_skipped}")
        print(f"   Errors encountered: {result.errors_encountered}")
        print(f"   Success rate: {result.success_rate:.1f}%")
        print("   " + "-"*50)
        
        if result.sources_processed:
            print("\n5. SOURCES PROCESSED")
            for source, count in result.sources_processed.items():
                print(f"   - {source}: {count} articles")
        
        if result.error_details:
            print("\n6. ERRORS ENCOUNTERED")
            for error in result.error_details[:5]:
                print(f"   - {error['source']}: {error.get('error', 'Unknown error')}")
        
        # Get stats
        print("\n7. DATABASE STATISTICS")
        stats = service.get_stats()
        print(f"   Total articles in DB: {stats['total_articles']}")
        print(f"   Total sources in DB: {stats['total_sources']}")
        print(f"   Total categories in DB: {stats['total_categories']}")
        
        # Verify result
        print("\n8. TEST RESULT")
        if result.total_articles_saved > 0:
            print("   ✅ INGESTION SUCCESSFUL - Articles were saved to database")
            return True
        else:
            print("   ⚠️  WARNING - No articles were saved")
            print(f"   Articles found: {result.total_articles_found}")
            print(f"   Duplicates: {result.duplicates_skipped}")
            print(f"   Errors: {result.errors_encountered}")
            if result.error_details:
                print("   First error:")
                print(f"     {result.error_details[0]}")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        service.close()
        Session.close()
        print("\n" + "="*60)


if __name__ == "__main__":
    success = test_ingestion_service()
    sys.exit(0 if success else 1)
