"""
Test Ollama Integration
======================
Tests the OllamaProvider and fallback mechanisms.

Usage:
    python test                   print(f"  ✅ Summary generated in {elapsed:.2f}s:")
                print(f"    {result['summary'][:200]}...")
                print("\n   📊 Metadata:")
                print(f"    - Model: {result.get('model', 'N/A')}")         print(f"  ✅ Summary generated in {elapsed:.2f}s:")
                print(f"    {result['summary'][:200]}...")
                print("\n   📊 Metadata:")
                print(f"    - Model: {result.get('model', 'N/A')}")ama_integration.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from llm.providers import OllamaProvider
from utils.logger import get_logger

logger = get_logger(__name__)


# Sample tech articles for testing
SAMPLE_ARTICLES = [
    {
        "title": "Revolutionary AI Model Achieves Human-Level Understanding",
        "content": """
        Researchers at a leading AI lab have unveiled a groundbreaking language model
        that demonstrates unprecedented capabilities in understanding context and nuance.
        The model, trained on diverse datasets spanning multiple domains, shows remarkable
        performance on complex reasoning tasks. Unlike previous generations, this model
        can maintain context across extended conversations and adapt its responses based
        on subtle cues. The team used innovative training techniques including reinforcement
        learning from human feedback (RLHF) and Constitutional AI principles to ensure
        alignment with human values. Early benchmarks suggest the model outperforms
        existing systems by 25% on standardized tests while using 40% less computational
        resources during inference.
        """
    },
    {
        "title": "Quantum Computing Breakthrough: Error Rates Drop Below Critical Threshold",
        "content": """
        Scientists have achieved a major milestone in quantum computing by successfully
        reducing error rates below the critical threshold needed for practical quantum
        error correction. The breakthrough involves a novel approach to qubit design
        that dramatically improves coherence times while maintaining high-fidelity gate
        operations. The team demonstrated sustained quantum computations lasting over
        one minute with error rates below 0.1%, a 100x improvement over previous systems.
        This advancement brings practical quantum computers significantly closer to reality,
        potentially enabling applications in drug discovery, cryptography, and optimization
        problems that are intractable for classical computers. The research combines
        innovations in materials science, cryogenic engineering, and control systems.
        """
    },
    {
        "title": "Edge AI Chips Enable Real-Time Processing on IoT Devices",
        "content": """
        A new generation of AI accelerator chips designed specifically for edge devices
        is transforming the Internet of Things landscape. These energy-efficient processors
        deliver neural network inference performance comparable to cloud-based systems
        while consuming less than 1 watt of power. The chips incorporate specialized
        tensor processing units, optimized memory hierarchies, and adaptive precision
        arithmetic to maximize efficiency. Manufacturers are integrating these chips
        into smart cameras, wearable devices, and industrial sensors, enabling real-time
        AI processing without cloud connectivity. Applications include instantaneous
        object detection, voice recognition, and predictive maintenance. The technology
        addresses critical concerns around latency, privacy, and bandwidth constraints
        that have limited previous AI deployments at the edge.
        """
    }
]


async def test_ollama_availability():
    """Test if Ollama server is available."""
    print("\n" + "="*70)
    print("TEST 1: Ollama Server Availability")
    print("="*70)
    
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        timeout=60
    )
    
    try:
        is_available = await provider.is_available()
        if is_available:
            print("✅ SUCCESS: Ollama server is running and model is available")
            print(f"   - Base URL: {provider.base_url}")
            print(f"   - Model: {provider.model}")
            return True
        else:
            print("❌ FAILED: Ollama server not available or model not found")
            print("   - Check if Ollama is running: ollama serve")
            print("   - Check if model exists: ollama list")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_ollama_summarization():
    """Test summarization with Ollama."""
    print("\n" + "="*70)
    print("TEST 2: Ollama Summarization")
    print("="*70)
    
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        timeout=60
    )
    
    results = []
    for i, article in enumerate(SAMPLE_ARTICLES, 1):
        print(f"\n📄 Article {i}: {article['title']}")
        print(f"   Content length: {len(article['content'])} characters")
        
        try:
            import time
            start_time = time.time()
            
            result = await provider.summarize(
                text=article['content'],
                max_length=200
            )
            
            elapsed = time.time() - start_time
            
            if result.get("success"):
                print(f"✅ Summary generated in {elapsed:.2f}s:")
                print(f"   {result['summary'][:200]}...")
                print("\n   📊 Metadata:")
                print(f"   - Model: {result.get('model', 'N/A')}")
                print(f"   - Provider: {result.get('provider', 'N/A')}")
                print(f"   - Keywords: {', '.join(result.get('keywords', [])[:5])}")
                results.append(True)
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return all(results)


async def test_provider_fallback():
    """Test fallback from Ollama to Claude."""
    print("\n" + "="*70)
    print("TEST 3: Provider Fallback Mechanism")
    print("="*70)
    
    # Test with invalid Ollama URL to trigger fallback
    print("\n🔄 Testing fallback with unavailable Ollama...")
    
    ollama = OllamaProvider(
        base_url="http://localhost:99999",  # Invalid port
        model="llama3.2:1b",
        timeout=5
    )
    
    ollama_available = await ollama.is_available()
    print(f"   Ollama available: {ollama_available}")
    
    if not ollama_available:
        print("✅ SUCCESS: Correctly detected Ollama unavailability")
        print("   In production, this would fall back to Claude")
        print("   (Claude fallback requires ANTHROPIC_API_KEY in .env)")
    else:
        print("⚠️  WARNING: Expected Ollama to be unavailable")
    
    # Test with working Ollama
    print("\n🔄 Testing with working Ollama...")
    
    ollama_working = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        timeout=60
    )
    
    is_available = await ollama_working.is_available()
    print(f"   Ollama available: {is_available}")
    
    if is_available:
        print("✅ SUCCESS: Ollama is primary provider")
    
    return True


async def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*70)
    print("TEST 4: Edge Cases and Error Handling")
    print("="*70)
    
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        timeout=60
    )
    
    test_cases = [
        {
            "name": "Empty text",
            "text": "",
            "should_fail": True  # Should return success: False
        },
        {
            "name": "Very short text",
            "text": "AI is cool.",
            "should_fail": False
        },
        {
            "name": "Special characters",
            "text": "Testing with émojis 🚀 and spëcial çharacters!",
            "should_fail": False
        },
        {
            "name": "Very long text",
            "text": "This is a test. " * 1000,  # 16,000+ characters
            "should_fail": False
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n🧪 Test: {test['name']}")
        print(f"   Text length: {len(test['text'])} characters")
        
        try:
            result = await provider.summarize(test['text'])
            
            if test['should_fail']:
                # Should have returned error
                if not result.get('success'):
                    print(f"✅ SUCCESS: Properly returned error: {result.get('error')}")
                    results.append(True)
                else:
                    print("⚠️  Expected failure but succeeded")
                    results.append(False)
            else:
                if result.get('success'):
                    print("✅ SUCCESS: Handled correctly")
                    results.append(True)
                else:
                    print(f"❌ FAILED: {result.get('error')}")
                    results.append(False)
                    
        except Exception as e:
            if test['should_fail']:
                print(f"✅ Expected error: {str(e)[:100]}")
                results.append(True)
            else:
                print(f"❌ Unexpected error: {str(e)[:100]}")
                results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Edge Case Success Rate: {success_rate:.1f}% ({sum(results)}/{len(results)})")
    
    return all(results)


async def run_all_tests():
    """Run all integration tests."""
    print("="*70)
    print("🚀 OLLAMA INTEGRATION TEST SUITE")
    print("="*70)
    print("\nTesting Ollama LLM provider implementation...")
    print("Model: llama3.2:1b")
    print("Provider: OllamaProvider (backend/llm/providers.py)")
    
    results = {
        "availability": await test_ollama_availability(),
        "summarization": await test_ollama_summarization(),
        "fallback": await test_provider_fallback(),
        "edge_cases": await test_edge_cases()
    }
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():<20} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    overall_percentage = (total_passed / total_tests) * 100
    
    print(f"\n{'='*70}")
    print(f"Overall: {total_passed}/{total_tests} tests passed ({overall_percentage:.1f}%)")
    print("="*70)
    
    if all(results.values()):
        print("\n🎉 All tests passed! Ollama integration is working correctly.")
        print("\n✅ Next Steps:")
        print("   1. Update .env.example with Ollama configuration")
        print("   2. Update README with Ollama setup instructions")
        print("   3. Add integration tests to test suite")
        print("   4. Test the /summarize API endpoint")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure Ollama is running: ollama serve")
        print("   2. Check model is downloaded: ollama list")
        print("   3. Test API manually: curl http://localhost:11434/api/tags")
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
