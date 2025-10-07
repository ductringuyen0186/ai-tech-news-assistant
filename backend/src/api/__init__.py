"""
API Package
==========

FastAPI application structure for the AI Tech News Assistant.
Contains route definitions, middleware, and API configuration.
"""

from .routes import api_router, root_router

__all__ = ["api_router", "root_router"]
