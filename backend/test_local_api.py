#!/usr/bin/env python
"""
Test Local API
=============
"""
import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test health
        response = await client.get("http://localhost:8000/health")
        print(f"Health: {response.status_code}")
        print(response.json())
        
        # Test API
        response = await client.get("http://localhost:8000/api/news?page=1&page_size=3")
        print(f"\nAPI: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total articles: {data['total']}")
            print(f"Articles in response: {len(data['items'])}")
            for article in data['items']:
                print(f"  - {article['title'][:60]}...")
        else:
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_api())
