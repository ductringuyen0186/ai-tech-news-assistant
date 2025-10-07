"""
Production Main Entry Point
============================

This module serves as the production entry point for the AI Tech News Assistant.
It re-exports the FastAPI app from the main module for compatibility with
deployment scripts and CI/CD pipelines.

For development, you can use main.py directly.
For production deployments, use this file.
"""

from main import app

__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    from utils.config import get_settings
    
    settings = get_settings()
    
    uvicorn.run(
        "production_main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Production mode - no hot reload
        log_level="info",
        access_log=True,
    )
