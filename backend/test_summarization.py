"""
Test Script for LLM Summarization
=================================

This script tests the LLM summarization functionality with sample article content.
Run this to verify that the summarization system is working correctly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm import ArticleSummarizer, LLMProviderType
from utils.logger import get_logger

logger = get_logger(__name__)

# Sample article content for testing
SAMPLE_ARTICLE = """
Title: OpenAI Announces GPT-4 Turbo with 128K Context Window

OpenAI has unveiled GPT-4 Turbo, the latest iteration of its flagship language model that comes with significant improvements over its predecessor. The most notable enhancement is the dramatically expanded context window, which can now handle up to 128,000 tokens - equivalent to about 100 pages of text.

This substantial increase in context length allows GPT-4 Turbo to process and maintain coherence across much longer documents, making it particularly valuable for applications requiring analysis of extensive texts, code repositories, or complex research papers.

The model also features updated training data with a knowledge cutoff of April 2023, compared to the previous version's cutoff of September 2021. This means GPT-4 Turbo has access to more recent information and can provide more current responses.

Performance improvements include faster response times and reduced costs, with OpenAI pricing the new model at $0.01 per 1,000 input tokens and $0.03 per 1,000 output tokens - representing a significant reduction from GPT-4's pricing.

Additionally, GPT-4 Turbo introduces enhanced function calling capabilities, improved instruction following, and better handling of complex reasoning tasks. The model is now available through OpenAI's API for developers and enterprise customers.

Industry experts see this release as OpenAI's response to increasing competition in the large language model space, particularly from models like Claude-2 and open-source alternatives. The expanded context window addresses one of the key limitations that developers have faced when building applications with previous versions of GPT-4.
"""


async def test_provider_status():
    """Test provider availability and status."""
    print("🔍 Checking LLM provider status...")
    
    summarizer = ArticleSummarizer()
    status = await summarizer.get_provider_status()
    
    print("📊 Provider Status:")
    print(f"   Available providers: {status['available_count']}")
    print(f"   Default provider: {status['default_provider']}")
    
    for provider_name, provider_info in status['providers'].items():
        status_icon = "✅" if provider_info['available'] else "❌"
        print(f"   {status_icon} {provider_name}: {provider_info}")
    
    return status['available_count'] > 0


async def test_summarization():
    """Test article summarization."""
    print("\n📝 Testing article summarization...")
    
    summarizer = ArticleSummarizer()
    
    try:
        # Test with auto provider selection
        result = await summarizer.summarize_article(
            article_text=SAMPLE_ARTICLE,
            title="OpenAI Announces GPT-4 Turbo with 128K Context Window",
            provider=LLMProviderType.AUTO
        )
        
        print("✅ Summarization successful!")
        print(f"   Provider used: {result.get('provider', 'unknown')}")
        print(f"   Model: {result.get('model', 'unknown')}")
        print(f"   Original length: {result.get('original_length', 0)} chars")
        print(f"   Summary length: {result.get('summary_length', 0)} chars")
        print(f"   Compression ratio: {result.get('compression_ratio', 0)}")
        print("\n📄 Summary:")
        print(f"   {result.get('summary', 'No summary generated')}")
        print(f"\n🏷️  Keywords: {result.get('keywords', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Summarization failed: {str(e)}")
        return False


async def test_specific_providers():
    """Test specific providers if available."""
    print("\n🧪 Testing specific providers...")
    
    summarizer = ArticleSummarizer()
    available_providers = await summarizer.get_available_providers()
    
    test_text = "Artificial intelligence is transforming the technology industry with new breakthroughs in machine learning, natural language processing, and computer vision. Companies are investing heavily in AI research and development to stay competitive."
    
    for provider_name in available_providers:
        try:
            provider_enum = LLMProviderType(provider_name)
            print(f"\n   Testing {provider_name}...")
            
            result = await summarizer.summarize_article(
                article_text=test_text,
                title="AI Technology Trends",
                provider=provider_enum
            )
            
            print(f"   ✅ {provider_name}: {result.get('summary', 'No summary')[:100]}...")
            
        except Exception as e:
            print(f"   ❌ {provider_name}: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 LLM Summarization Test Suite")
    print("=" * 50)
    
    # Test 1: Check provider status
    has_providers = await test_provider_status()
    
    if not has_providers:
        print("\n⚠️  No LLM providers are available!")
        print("   To test summarization:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Run: ollama pull llama3.2")
        print("   3. Or set ANTHROPIC_API_KEY environment variable")
        return
    
    # Test 2: Full summarization test
    success = await test_summarization()
    
    if success:
        # Test 3: Test specific providers
        await test_specific_providers()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Summarization test failed. Check provider configuration.")


if __name__ == "__main__":
    asyncio.run(main())
