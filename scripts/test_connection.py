"""
Test Backend Connection
=======================
Quick diagnostic script to test if backend is accessible
"""
import httpx
import asyncio

async def test_backend():
    """Test all backend endpoints"""
    base_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000"
    ]
    
    endpoints = [
        "/",
        "/health",
        "/ping",
        "/articles"
    ]
    
    print("🔍 Testing Backend Connectivity")
    print("=" * 50)
    
    for base_url in base_urls:
        print(f"\n🌐 Testing {base_url}")
        print("-" * 50)
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    print(f"✅ {endpoint:20} | Status: {response.status_code} | OK")
            except httpx.ConnectError:
                print(f"❌ {endpoint:20} | Connection refused")
            except httpx.TimeoutException:
                print(f"⏱️  {endpoint:20} | Timeout")
            except Exception as e:
                print(f"❌ {endpoint:20} | Error: {str(e)[:40]}")
    
    print("\n" + "=" * 50)
    print("✅ If you see green checkmarks above, backend is working!")
    print("📝 Copy the working base URL to your frontend configuration")

if __name__ == "__main__":
    asyncio.run(test_backend())
