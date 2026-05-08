"""
Agent Skills Package
====================

This package contains the four LangChain ``@tool``-decorated skills that the
deepagents-based research agent calls during a per-article reasoning run
(Mission 2, Milestone 2). Each skill is a thin async wrapper around an
existing service:

* ``search_articles``      — semantic retrieval via :class:`SearchService`
* ``summarize_article``    — cache-aware summary via :class:`SummarizationService`
* ``extract_entities``     — NER + persistence via :class:`EntityExtractionService`
* ``query_knowledge_graph``— co-mention walk over the entity graph

All four are async tool bodies (per the spike's gotcha note: synchronous
``@tool`` bodies that call ``asyncio.run`` blow up when invoked from
inside FastAPI's running event loop). LangGraph dispatches async tools
natively, so no thread hopping is needed.

Skills return JSON strings (LLMs only see text). Callers that need
structured data should ``json.loads`` the return value.
"""

from .search_articles import search_articles
from .summarize_article import summarize_article
from .extract_entities import extract_entities
from .query_knowledge_graph import query_knowledge_graph

__all__ = [
    "search_articles",
    "summarize_article",
    "extract_entities",
    "query_knowledge_graph",
]
