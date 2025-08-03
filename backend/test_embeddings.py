"""
Test Script for Embedding Generation
====================================

This script tests the embedding generation functionality and database integration.
"""

import asyncio
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vectorstore.embeddings import EmbeddingGenerator, generate_article_embeddings
from manage_embeddings import ArticleEmbeddingManager
from utils.logger import get_logger

logger = get_logger(__name__)

# Sample test articles
TEST_ARTICLES = [
    {
        "id": 1,
        "title": "Breakthrough in Quantum Computing",
        "content": """
        Researchers at MIT have achieved a significant breakthrough in quantum computing by developing 
        a new quantum error correction method. This advancement could bring practical quantum computers 
        closer to reality. The team demonstrated stable quantum states that lasted 100 times longer 
        than previous attempts, marking a crucial step toward fault-tolerant quantum computation.
        
        The quantum error correction technique uses a novel approach to detect and fix quantum bit 
        errors in real-time without destroying the quantum information. This has been one of the 
        biggest challenges in quantum computing development.
        """,
        "source": "MIT Tech Review",
        "url": "https://example.com/quantum-breakthrough",
        "published_date": "2024-01-15"
    },
    {
        "id": 2,
        "title": "AI Language Model Achieves Human-Level Performance",
        "content": """
        A new large language model has achieved human-level performance on multiple standardized tests, 
        including reading comprehension, mathematical reasoning, and scientific problem-solving. 
        The model, trained on a diverse dataset of text and code, demonstrates remarkable abilities 
        in understanding context and generating coherent responses.
        
        What sets this model apart is its ability to explain its reasoning process, making it more 
        interpretable and trustworthy for critical applications. The researchers believe this 
        represents a significant step toward artificial general intelligence.
        """,
        "source": "AI Research Journal",
        "url": "https://example.com/ai-breakthrough",
        "published_date": "2024-01-20"
    },
    {
        "id": 3,
        "title": "Revolutionary Battery Technology Extends EV Range",
        "content": """
        A startup has developed a revolutionary solid-state battery technology that could triple 
        the range of electric vehicles while reducing charging time to just 5 minutes. The new 
        batteries use a proprietary solid electrolyte that eliminates the fire risk associated 
        with traditional lithium-ion batteries.
        
        Initial tests show the batteries maintain 95% of their capacity after 10,000 charge 
        cycles, far exceeding current battery technology. Major automotive manufacturers are 
        already expressing interest in licensing the technology for their next-generation EVs.
        """,
        "source": "CleanTech News",
        "url": "https://example.com/battery-breakthrough",
        "published_date": "2024-01-25"
    }
]


async def test_embedding_generator():
    """Test the basic embedding generator functionality."""
    print("🧪 Testing Embedding Generator")
    print("-" * 40)
    
    try:
        generator = EmbeddingGenerator()
        
        # Test model loading
        print("Loading embedding model...")
        await generator.load_model()
        model_info = generator.get_model_info()
        print(f"✅ Model loaded: {model_info['model_name']}")
        print(f"   Dimensions: {model_info['embedding_dim']}")
        print(f"   Device: {model_info['device']}")
        
        # Test single text embedding
        print("\nTesting single text embedding...")
        test_text = "Artificial intelligence is transforming technology."
        embedding = await generator.generate_embeddings(test_text)
        print(f"✅ Generated embedding shape: {embedding.shape}")
        
        # Test batch embedding
        print("\nTesting batch embedding...")
        test_texts = [article["content"][:200] for article in TEST_ARTICLES]
        embeddings = await generator.generate_embeddings(test_texts)
        print(f"✅ Generated batch embeddings shape: {embeddings.shape}")
        
        # Test article embedding
        print("\nTesting article embedding...")
        embedded_articles = await generator.embed_articles(TEST_ARTICLES)
        print(f"✅ Embedded {len(embedded_articles)} articles")
        
        for i, article in enumerate(embedded_articles):
            print(f"   Article {i+1}: {len(article['embedding'])} dimensions")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generator test failed: {str(e)}")
        return False
    finally:
        if 'generator' in locals():
            await generator.cleanup()


async def test_database_integration():
    """Test database integration with embeddings."""
    print("\n🗄️  Testing Database Integration")
    print("-" * 40)
    
    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Create test database with articles
        print("Creating test database...")
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            
            # Create articles table
            cursor.execute("""
                CREATE TABLE articles (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    url TEXT,
                    published_date TEXT
                )
            """)
            
            # Insert test articles
            for article in TEST_ARTICLES:
                cursor.execute("""
                    INSERT INTO articles (id, title, content, source, url, published_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    article["id"],
                    article["title"],
                    article["content"],
                    article["source"],
                    article["url"],
                    article["published_date"]
                ))
            
            conn.commit()
        
        print(f"✅ Created test database with {len(TEST_ARTICLES)} articles")
        
        # Test embedding manager
        print("\nTesting embedding manager...")
        manager = ArticleEmbeddingManager(db_path=temp_db_path)
        
        # Set up database schema
        await manager.setup_database()
        print("✅ Database schema updated for embeddings")
        
        # Get initial statistics
        initial_stats = await manager.get_embedding_statistics()
        print(f"✅ Initial stats: {initial_stats}")
        
        # Process articles
        print("\nProcessing articles for embeddings...")
        summary = await manager.process_all_articles(batch_size=2)
        print(f"✅ Processing complete: {summary}")
        
        # Verify embeddings in database
        print("\nVerifying embeddings in database...")
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, embedding_model, embedding_dim
                FROM articles 
                WHERE embedding IS NOT NULL
            """)
            embedded_rows = cursor.fetchall()
            
            print(f"✅ Found {len(embedded_rows)} articles with embeddings")
            for row in embedded_rows:
                print(f"   Article {row[0]}: {row[1][:30]}... | Model: {row[2]} | Dim: {row[3]}")
        
        await manager.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False
    finally:
        # Clean up temporary database
        try:
            os.unlink(temp_db_path)
        except:
            pass


async def test_similarity_computation():
    """Test similarity computation between embeddings."""
    print("\n🔍 Testing Similarity Computation")
    print("-" * 40)
    
    try:
        generator = EmbeddingGenerator()
        await generator.load_model()
        
        # Generate embeddings for test articles
        embedded_articles = await generator.embed_articles(TEST_ARTICLES)
        
        # Extract embeddings as numpy arrays
        import numpy as np
        embeddings = np.array([article["embedding"] for article in embedded_articles])
        
        # Test query
        query_text = "quantum computing breakthrough research"
        query_embedding = await generator.generate_embeddings(query_text)
        
        # Compute similarities
        similarities = await generator.compute_similarity(
            query_embedding[0],  # Single embedding
            embeddings
        )
        
        print(f"✅ Computed similarities for query: '{query_text}'")
        print("   Similarity scores:")
        
        # Sort by similarity
        for i, score in enumerate(similarities):
            article = embedded_articles[i]
            print(f"   {score:.3f}: {article['title']}")
        
        # Find most similar article
        best_match_idx = np.argmax(similarities)
        best_article = embedded_articles[best_match_idx]
        print(f"\n🎯 Best match: {best_article['title']} (score: {similarities[best_match_idx]:.3f})")
        
        await generator.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Similarity computation test failed: {str(e)}")
        return False


async def test_convenience_functions():
    """Test convenience functions for easy usage."""
    print("\n⚡ Testing Convenience Functions")
    print("-" * 40)
    
    try:
        # Test the convenience function
        embedded_articles = await generate_article_embeddings(TEST_ARTICLES)
        print(f"✅ Convenience function embedded {len(embedded_articles)} articles")
        
        # Verify embeddings exist
        for article in embedded_articles:
            assert "embedding" in article
            assert "embedding_model" in article
            assert "embedding_dim" in article
            print(f"   {article['title'][:30]}... | Dim: {article['embedding_dim']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {str(e)}")
        return False


async def main():
    """Run all embedding tests."""
    print("🚀 Embedding System Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Basic embedding generator
    result1 = await test_embedding_generator()
    test_results.append(("Embedding Generator", result1))
    
    # Test 2: Database integration
    result2 = await test_database_integration()
    test_results.append(("Database Integration", result2))
    
    # Test 3: Similarity computation
    result3 = await test_similarity_computation()
    test_results.append(("Similarity Computation", result3))
    
    # Test 4: Convenience functions
    result4 = await test_convenience_functions()
    test_results.append(("Convenience Functions", result4))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! Embedding system is ready for use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
        if passed == 0:
            print("\n💡 If all tests failed, you may need to install dependencies:")
            print("   pip install sentence-transformers torch")


if __name__ == "__main__":
    asyncio.run(main())
