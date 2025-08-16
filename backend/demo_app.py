"""
Demo FastAPI Application
========================

A standalone FastAPI app for demonstrating AI/ML features.
Run this to showcase the AI Tech News Assistant capabilities.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Import demo router
from api_demo import router as demo_router

# Create FastAPI app
app = FastAPI(
    title="AI Tech News Assistant - Demo",
    description="Demo application showcasing AI/ML features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include demo router
app.include_router(demo_router)


@app.get("/")
async def root():
    """Root endpoint with demo information."""
    return {
        "message": "AI Tech News Assistant - Demo API",
        "version": "1.0.0",
        "features": [
            "News Ingestion from RSS feeds",
            "AI-Powered Summarization",
            "Semantic Embeddings Generation", 
            "Vector Search & Similarity",
            "RAG Query Interface"
        ],
        "endpoints": {
            "demo": "/docs#/AI/ML%20Demo",
            "interactive_docs": "/docs",
            "status": "/demo/status",
            "features": "/demo/features"
        },
        "tech_stack": {
            "backend": "FastAPI",
            "ai_ml": "Sentence Transformers + LangChain",
            "llm": "Ollama + Claude",
            "embeddings": "HuggingFace Transformers"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-tech-news-demo"}


if __name__ == "__main__":
    print("🚀 Starting AI Tech News Assistant Demo")
    print("📖 Documentation: http://localhost:8000/docs")
    print("🎯 Demo Features: http://localhost:8000/demo/features")
    print("📊 Demo Status: http://localhost:8000/demo/status")
    
    uvicorn.run(
        "demo_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
