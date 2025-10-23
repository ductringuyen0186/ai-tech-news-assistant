#!/usr/bin/env python
"""
Seed Sample Articles into Database
==================================

Creates sample tech news articles for testing and demo purposes.
"""

import sqlite3
from datetime import datetime, timedelta
import json

# Sample articles data
SAMPLE_ARTICLES = [
    {
        "title": "OpenAI Releases GPT-5 with Revolutionary Capabilities",
        "content": "OpenAI has announced the release of GPT-5, featuring unprecedented improvements in reasoning, multimodal understanding, and reduced hallucinations. The model demonstrates human-level performance across various benchmark tests.",
        "url": "https://techcrunch.com/article/openai-gpt5-release",
        "source": "TechCrunch",
        "categories": ["AI", "Machine Learning"],
        "published_at": datetime.now() - timedelta(days=1)
    },
    {
        "title": "Google Announces Quantum Chip Breakthrough",
        "content": "Google's Quantum AI team has unveiled a new quantum chip achieving quantum advantage in practical problems. The advancement brings quantum computing closer to real-world applications.",
        "url": "https://theverge.com/quantum-chip",
        "source": "The Verge",
        "categories": ["Quantum Computing", "Hardware"],
        "published_at": datetime.now() - timedelta(days=2)
    },
    {
        "title": "Critical Security Vulnerability in Popular Framework",
        "content": "Security researchers have discovered a critical zero-day vulnerability in a widely-used web framework affecting millions of applications. Patches have been released urgently.",
        "url": "https://wired.com/security-vulnerability",
        "source": "Wired",
        "categories": ["Security", "Software"],
        "published_at": datetime.now() - timedelta(days=3)
    },
    {
        "title": "New Programming Language Gains Adoption",
        "content": "A new systems programming language combining performance of Rust with developer experience of Python has gained significant adoption among enterprise developers.",
        "url": "https://news.ycombinator.com/item",
        "source": "Hacker News",
        "categories": ["Programming Languages", "Development"],
        "published_at": datetime.now() - timedelta(days=4)
    },
    {
        "title": "AI Models Show Promise in Drug Discovery",
        "content": "Researchers demonstrate that AI models can accelerate pharmaceutical drug discovery, identifying promising compounds 10x faster than traditional methods.",
        "url": "https://nature.com/ai-drug-discovery",
        "source": "Nature",
        "categories": ["AI", "Healthcare"],
        "published_at": datetime.now() - timedelta(days=5)
    },
    {
        "title": "Cloud Provider Reports Record Q3 Growth",
        "content": "Major cloud provider reports record revenue growth driven by increased enterprise adoption of AI and machine learning services.",
        "url": "https://finance.yahoo.com/cloud-earnings",
        "source": "Yahoo Finance",
        "categories": ["Cloud Computing", "Business"],
        "published_at": datetime.now() - timedelta(days=6)
    },
    {
        "title": "Blockchain Technology Powers New Supply Chain Solutions",
        "content": "Companies are leveraging blockchain for transparent supply chain tracking, reducing fraud and improving efficiency across industries.",
        "url": "https://forbes.com/blockchain-supply-chain",
        "source": "Forbes",
        "categories": ["Blockchain", "Enterprise"],
        "published_at": datetime.now() - timedelta(days=7)
    },
    {
        "title": "Machine Learning Reduces Energy Consumption in Data Centers",
        "content": "Tech giants deploy ML algorithms to optimize data center cooling, reducing energy consumption by 40% and cutting carbon emissions.",
        "url": "https://arstechnica.com/ml-datacenters",
        "source": "Ars Technica",
        "categories": ["Machine Learning", "Sustainability"],
        "published_at": datetime.now() - timedelta(days=8)
    }
]


def create_articles_table(conn):
    """Create articles table if it doesn't exist."""
    cursor = conn.cursor()
    
    # Drop if exists for fresh start
    cursor.execute("DROP TABLE IF EXISTS articles")
    
    cursor.execute("""
        CREATE TABLE articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            published_at TIMESTAMP NOT NULL,
            source TEXT NOT NULL,
            categories JSON,
            keywords JSON,
            ai_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("✓ Created articles table")


def seed_articles(conn):
    """Insert sample articles into database."""
    cursor = conn.cursor()
    
    for i, article in enumerate(SAMPLE_ARTICLES):
        # Generate ID from URL
        import hashlib
        article_id = hashlib.sha256(article["url"].encode()).hexdigest()[:16]
        
        cursor.execute("""
            INSERT INTO articles 
            (id, title, content, url, published_at, source, categories, keywords, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            article["title"],
            article["content"],
            article["url"],
            article["published_at"].isoformat(),
            article["source"],
            json.dumps(article["categories"]),
            json.dumps([]),  # Empty keywords for now
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    conn.commit()
    print(f"✓ Seeded {len(SAMPLE_ARTICLES)} articles")


def verify_articles(conn):
    """Verify articles were inserted correctly."""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    print(f"✓ Total articles in database: {count}")
    
    # Show first few articles
    cursor.execute("SELECT id, title, source FROM articles LIMIT 3")
    for row in cursor.fetchall():
        print(f"  - [{row[0][:8]}...] {row[1][:50]}... ({row[2]})")


if __name__ == "__main__":
    print("🌱 Seeding sample articles...")
    
    try:
        conn = sqlite3.connect("news_assistant.db")
        
        # Create fresh table
        create_articles_table(conn)
        
        # Seed articles
        seed_articles(conn)
        
        # Verify
        verify_articles(conn)
        
        conn.close()
        print("\n✅ Successfully seeded articles database!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
