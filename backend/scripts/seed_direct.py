#!/usr/bin/env python
"""
Direct Database Seeding Script
==============================

Seeds the production PostgreSQL database directly using SQLAlchemy.
This bypasses the API and works even if routes aren't loading.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Sample articles
SAMPLE_ARTICLES = [
    {
        "title": "OpenAI Releases GPT-5 with Revolutionary Capabilities",
        "content": "OpenAI has announced the release of GPT-5, featuring unprecedented improvements in reasoning, multimodal understanding, and reduced hallucinations. The model demonstrates human-level performance across various benchmark tests.",
        "url": "https://techcrunch.com/2025/11/16/openai-gpt5-release",
        "source": "techcrunch",
        "author": "TechCrunch Staff",
        "published_date": datetime.now() - timedelta(days=1)
    },
    {
        "title": "Google Announces Quantum Chip Breakthrough",
        "content": "Google's Quantum AI team has unveiled a new quantum chip achieving quantum advantage in practical problems. The advancement brings quantum computing closer to real-world applications.",
        "url": "https://theverge.com/2025/11/15/google-quantum-chip",
        "source": "theverge",
        "author": "The Verge Team",
        "published_date": datetime.now() - timedelta(days=2)
    },
    {
        "title": "Critical Security Vulnerability in Popular Framework",
        "content": "Security researchers have discovered a critical zero-day vulnerability in a widely-used web framework affecting millions of applications. Patches have been released urgently.",
        "url": "https://wired.com/2025/11/14/security-vulnerability",
        "source": "wired",
        "author": "Security Desk",
        "published_date": datetime.now() - timedelta(days=3)
    },
    {
        "title": "New Programming Language Gains Rapid Adoption",
        "content": "A new systems programming language combining performance of Rust with developer experience of Python has gained significant adoption among enterprise developers.",
        "url": "https://news.ycombinator.com/item?id=38234567",
        "source": "hackernews",
        "author": "HN Community",
        "published_date": datetime.now() - timedelta(days=4)
    },
    {
        "title": "AI Models Show Promise in Drug Discovery",
        "content": "Researchers demonstrate that AI models can accelerate pharmaceutical drug discovery, identifying promising compounds 10x faster than traditional methods.",
        "url": "https://nature.com/articles/ai-drug-discovery-2025",
        "source": "nature",
        "author": "Nature Research",
        "published_date": datetime.now() - timedelta(days=5)
    },
    {
        "title": "Cloud Provider Reports Record Q3 Growth",
        "content": "Major cloud provider reports record revenue growth driven by increased enterprise adoption of AI and machine learning services.",
        "url": "https://finance.yahoo.com/news/cloud-earnings-q3-2025",
        "source": "yahoo",
        "author": "Finance Team",
        "published_date": datetime.now() - timedelta(days=6)
    },
    {
        "title": "Blockchain Powers New Supply Chain Solutions",
        "content": "Companies are leveraging blockchain for transparent supply chain tracking, reducing fraud and improving efficiency across industries.",
        "url": "https://forbes.com/2025/11/10/blockchain-supply-chain",
        "source": "forbes",
        "author": "Forbes Contributors",
        "published_date": datetime.now() - timedelta(days=7)
    },
    {
        "title": "ML Reduces Energy Use in Data Centers by 40%",
        "content": "Tech giants deploy ML algorithms to optimize data center cooling, reducing energy consumption by 40% and cutting carbon emissions significantly.",
        "url": "https://arstechnica.com/2025/11/09/ml-datacenters-efficiency",
        "source": "arstechnica",
        "author": "Ars Technical Staff",
        "published_date": datetime.now() - timedelta(days=8)
    }
]


def generate_article_id(url: str) -> str:
    """Generate a unique ID for an article based on its URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def seed_database():
    """Seed the database with sample articles."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("   Set it with: $env:DATABASE_URL='postgresql://...'")
        return False
    
    # Fix postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"\n{'='*60}")
    print("🌱 DIRECT DATABASE SEEDING")
    print(f"{'='*60}\n")
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    print(f"📝 Articles to seed: {len(SAMPLE_ARTICLES)}\n")
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if articles table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'articles'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            print("⚠️  Articles table doesn't exist. Creating it...\n")
            # Create table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS articles (
                    id VARCHAR PRIMARY KEY,
                    title VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    url VARCHAR UNIQUE NOT NULL,
                    source VARCHAR NOT NULL,
                    author VARCHAR,
                    published_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            print("✅ Table created successfully\n")
        
        # Insert articles
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for idx, article in enumerate(SAMPLE_ARTICLES, 1):
            try:
                article_id = generate_article_id(article["url"])
                
                # Check if article already exists
                result = session.execute(
                    text("SELECT id FROM articles WHERE id = :id"),
                    {"id": article_id}
                )
                if result.first():
                    print(f"⏭️  [{idx}/{len(SAMPLE_ARTICLES)}] Skipped (exists): {article['title'][:50]}...")
                    skip_count += 1
                    continue
                
                # Insert article
                session.execute(text("""
                    INSERT INTO articles (id, title, content, url, source, author, published_date)
                    VALUES (:id, :title, :content, :url, :source, :author, :published_date)
                """), {
                    "id": article_id,
                    "title": article["title"],
                    "content": article["content"],
                    "url": article["url"],
                    "source": article["source"],
                    "author": article["author"],
                    "published_date": article["published_date"]
                })
                session.commit()
                
                print(f"✅ [{idx}/{len(SAMPLE_ARTICLES)}] {article['title'][:50]}...")
                success_count += 1
                
            except Exception as e:
                session.rollback()
                print(f"❌ [{idx}/{len(SAMPLE_ARTICLES)}] Error: {str(e)[:100]}")
                error_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully seeded: {success_count} articles")
        if skip_count > 0:
            print(f"⏭️  Skipped (already exist): {skip_count} articles")
        if error_count > 0:
            print(f"❌ Failed: {error_count} articles")
        print(f"{'='*60}\n")
        
        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM articles"))
        total = result.scalar()
        print(f"📊 Total articles in database: {total}\n")
        
        # Show sample articles
        result = session.execute(text("SELECT title, source FROM articles ORDER BY published_date DESC LIMIT 3"))
        print("📰 Sample articles:")
        for row in result:
            print(f"   • {row[0][:60]}... ({row[1]})")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Database error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = seed_database()
    if success:
        print("\n✅ Seeding complete!")
        print("\n🌐 Test the API:")
        print("   curl 'https://ai-tech-news-assistant-backend.onrender.com/api/news?page=1&page_size=5'")
    else:
        print("\n❌ Seeding failed!")
        sys.exit(1)
