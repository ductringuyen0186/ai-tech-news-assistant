"""
AI Tech News Assistant
====================
Production-grade news scraping and AI analysis platform

This is the main entry point for the application.
Run with: python main.py
"""
import logging
import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from production_main import app, settings, logger
except ImportError as e:
    print(f"❌ Failed to import production backend: {e}")
    print("📁 Current directory:", os.getcwd())
    print("🔍 Backend path:", backend_path)
    print("🐍 Python path:", sys.path[:3])
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting AI Tech News Assistant")
    print("=" * 50)
    
    # Import here to avoid circular imports
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "production_main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        app_dir=str(backend_path)
    )