"""
Quick Manual Test Script
======================
Simple verification of the news scraping system
"""
import requests
import time
import json

def test_api_endpoints():
    """Test the main API endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing API Endpoints")
    print("=" * 30)
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   📊 Status: {health_data['status']}")
        print()
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test articles endpoint
    try:
        response = requests.get(f"{base_url}/articles", timeout=15)
        print(f"✅ Articles endpoint: {response.status_code}")
        if response.status_code == 200:
            articles_data = response.json()
            print(f"   📰 Total articles: {len(articles_data.get('articles', []))}")
            
            # Show sample article if available
            articles = articles_data.get('articles', [])
            if articles:
                sample = articles[0]
                print(f"   📄 Sample: {sample.get('title', 'No title')[:60]}...")
                print(f"   🔗 Source: {sample.get('source', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ Articles endpoint failed: {e}")
    
    # Test scrape endpoint
    try:
        print("🔄 Testing scrape endpoint (this may take a moment)...")
        response = requests.post(f"{base_url}/scrape", timeout=60)
        print(f"✅ Scrape endpoint: {response.status_code}")
        if response.status_code == 200:
            scrape_data = response.json()
            print(f"   🆕 New articles: {scrape_data.get('articles_added', 0)}")
            print(f"   📊 Total articles: {scrape_data.get('total_articles', 0)}")
        print()
    except Exception as e:
        print(f"❌ Scrape endpoint failed: {e}")
    
    # Test search endpoint
    try:
        search_query = "python"
        response = requests.get(f"{base_url}/search?q={search_query}", timeout=10)
        print(f"✅ Search endpoint: {response.status_code}")
        if response.status_code == 200:
            search_data = response.json()
            print(f"   🔍 Search '{search_query}': {len(search_data.get('articles', []))} results")
        print()
    except Exception as e:
        print(f"❌ Search endpoint failed: {e}")

def main():
    """Main test function"""
    print("🚀 AI Tech News Assistant - Manual API Test")
    print("=" * 50)
    print("⏳ Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    test_api_endpoints()
    
    print("🎉 Manual testing completed!")
    print("📖 Open http://127.0.0.1:8000/docs for full API documentation")

if __name__ == "__main__":
    main()