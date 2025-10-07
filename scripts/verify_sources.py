"""
Simple News Scraping Verification
================================
Test if we can successfully scrape news from our sources
"""
import httpx
import asyncio
from bs4 import BeautifulSoup
import json

async def test_hacker_news():
    """Test Hacker News API"""
    print("📰 Testing Hacker News API...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Get top stories
            response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            story_ids = response.json()[:5]  # Get top 5
            print(f"✅ Got {len(story_ids)} story IDs from HN")
            
            # Get details of first story
            if story_ids:
                story_response = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_ids[0]}.json")
                story = story_response.json()
                print(f"📄 Sample story: {story.get('title', 'No title')[:60]}...")
                print(f"🔗 URL: {story.get('url', 'No URL')}")
            
            return True
    except Exception as e:
        print(f"❌ Hacker News test failed: {e}")
        return False

async def test_reddit():
    """Test Reddit JSON API"""
    print("\n🔴 Testing Reddit API...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test programming subreddit
            headers = {"User-Agent": "AI Tech News Assistant/2.0"}
            response = await client.get("https://www.reddit.com/r/programming.json", headers=headers)
            data = response.json()
            
            posts = data.get("data", {}).get("children", [])
            print(f"✅ Got {len(posts)} posts from r/programming")
            
            if posts:
                sample_post = posts[0].get("data", {})
                print(f"📄 Sample post: {sample_post.get('title', 'No title')[:60]}...")
                print(f"👍 Score: {sample_post.get('score', 0)}")
            
            return True
    except Exception as e:
        print(f"❌ Reddit test failed: {e}")
        return False

async def test_github_trending():
    """Test GitHub trending scraping"""
    print("\n🐙 Testing GitHub Trending...")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {"User-Agent": "AI Tech News Assistant/2.0"}
            response = await client.get("https://github.com/trending", headers=headers)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            repos = soup.find_all('h2', class_='h3 lh-condensed')
            
            print(f"✅ Found {len(repos)} trending repositories")
            
            if repos:
                first_repo = repos[0].find('a')
                if first_repo:
                    repo_name = first_repo.get('href', '').strip('/')
                    print(f"📄 Sample repo: {repo_name}")
            
            return True
    except Exception as e:
        print(f"❌ GitHub trending test failed: {e}")
        return False

async def test_all_sources():
    """Test all news sources"""
    print("🧪 AI Tech News Assistant - Source Verification")
    print("=" * 55)
    
    results = []
    
    # Test each source
    results.append(await test_hacker_news())
    results.append(await test_reddit())
    results.append(await test_github_trending())
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"✅ Successful sources: {sum(results)}/3")
    print(f"❌ Failed sources: {3 - sum(results)}/3")
    
    if all(results):
        print("\n🎉 All news sources are working correctly!")
        print("🚀 Your production system is ready to scrape real news!")
    else:
        print("\n⚠️  Some sources failed - check your internet connection")
    
    return all(results)

if __name__ == "__main__":
    success = asyncio.run(test_all_sources())
    if success:
        print("\n▶️  Run 'python production_main.py' to start the full system")
        print("📖 API docs: http://127.0.0.1:8000/docs")
    else:
        print("\n🔧 Fix the failed sources before starting the full system")