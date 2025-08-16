"""
Simple Debug Backend - Minimal FastAPI for Testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data
ARTICLES = [
    {
        "id": "1",
        "title": "Test Article 1",
        "content": "This is a test article to check if the API is working. It contains detailed content about the topic.",
        "summary": "This is a test article to check if the API is working",
        "url": "https://example.com/1",
        "source": "Test Source",
        "published_at": datetime.now().isoformat(),
        "categories": ["Technology", "Testing"],
        "author": "Test Author",
        "metadata": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": "2", 
        "title": "Test Article 2",
        "content": "Another test article for debugging purposes. This article has more detailed content to test the display.",
        "summary": "Another test article for debugging purposes",
        "url": "https://example.com/2",
        "source": "Debug News",
        "published_at": datetime.now().isoformat(),
        "categories": ["Development", "Debugging"],
        "author": "Debug User",
        "metadata": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

@app.get("/")
async def root():
    return {"message": "Debug API is working!", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/news/articles")
async def get_articles():
    return {
        "articles": ARTICLES,
        "total": len(ARTICLES),
        "limit": 10,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/news/stats")
async def get_stats():
    return {
        "total_articles": len(ARTICLES),
        "categories": {"Technology": 1, "Development": 1},
        "sources": {"Test Source": 1, "Debug News": 1},
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/v1/news/categories")
async def get_categories():
    return {"categories": ["Technology", "Development"], "count": 2}

@app.get("/api/v1/news/sources")
async def get_sources():
    return {"sources": {"Test Source": 1, "Debug News": 1}, "count": 2}

if __name__ == "__main__":
    import uvicorn
    print("🔧 Starting DEBUG API on http://localhost:8000")
    print("🔧 CORS enabled for all origins")
    print("🔧 Test endpoints:")
    print("   - GET /")
    print("   - GET /api/v1/health")
    print("   - GET /api/v1/news/articles")
    uvicorn.run(app, host="127.0.0.1", port=8000)
