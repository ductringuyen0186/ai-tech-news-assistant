import requests
import json
import time

print("Testing local backend API...")
print("="*60)

# Wait a bit for server to start
time.sleep(1)

try:
    # Test health
    print("\n1. Testing health endpoint...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Test API
    print("\n2. Testing /api/news endpoint...")
    response = requests.get("http://localhost:8000/api/news?page=1&page_size=3", timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Total articles: {data.get('total', 0)}")
        print(f"   Page: {data.get('page', 0)}")
        print(f"   Articles returned: {len(data.get('items', []))}")
        print(f"\n   Sample articles:")
        for article in data.get('items', [])[:3]:
            print(f"     - {article.get('title', 'No title')[:60]}...")
    else:
        print(f"   Error: {response.text}")
    
    print("\n" + "="*60)
    print("✅ Backend is working!")
    
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Cannot connect to backend at http://localhost:8000")
    print("   Make sure the backend is running with:")
    print("   start-backend.bat")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
