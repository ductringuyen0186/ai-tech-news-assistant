#!/usr/bin/env python3
"""
RSS Ingestion CLI Tool
=====================

Simple command-line tool to test RSS feed ingestion functionality.
Use this to manually trigger RSS ingestion and test the pipeline.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.rss_feeds import ingest_tech_news
from utils.logger import setup_logging


async def main():
    """Main CLI function."""
    print("🚀 AI Tech News Assistant - RSS Ingestion Test")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    try:
        print("📡 Starting RSS feed ingestion...")
        summary = await ingest_tech_news()
        
        print("\n✅ Ingestion completed successfully!")
        print("\n📊 Summary:")
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
