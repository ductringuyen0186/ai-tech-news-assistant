"""
search_articles agent skill
===========================

Semantic-search tool the deepagents orchestrator calls to discover relevant
articles. Wraps :meth:`SearchService.search` and returns a stripped-down
list of hit dicts. The orchestrator NEVER sees raw article body text via
this tool — only id/title/source/snippet/score — which is the M4 prompt-
discipline contract documented in
``docs/notes/deepagents-api-surface.md`` section 7.

The tool is a LangChain ``@tool``-decorated async coroutine. LangGraph
dispatches it natively (no thread hopping). The docstring + type hints
ARE its JSON schema as far as the LLM is concerned, so keep them tight.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.tools import tool

from src.models.search import SearchRequest
from src.services.search_service import SearchService


logger = logging.getLogger(__name__)


# Module-level singleton so repeated tool calls don't re-init the embedding
# generator (a 384-dim sentence-transformers load is ~1s).
_search_service: Optional[SearchService] = None


def _get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service


# Cap defensively — the LLM has been known to ask for 100+.
_MIN_TOP_K = 1
_MAX_TOP_K = 25
_SNIPPET_CHARS = 300


@tool
async def search_articles(query: str, top_k: int = 5) -> str:
    """Semantic-search the local tech-news article corpus.

    Use this to discover article IDs relevant to a user question BEFORE
    calling ``summarize_article`` or ``extract_entities`` on a specific
    article. Returns ONLY id/title/source/snippet/score — no raw body
    text. Cite article IDs verbatim in your final answer.

    Args:
        query: Natural-language search query (e.g. "OpenAI GPT-5 release").
            Must be non-empty.
        top_k: How many top hits to return. Defaults to 5; clamped to
            [1, 25] to keep the tool payload bounded.

    Returns:
        A JSON string with shape::

            {
                "results": [
                    {
                        "article_id": int,
                        "title": str,
                        "source": str,
                        "snippet": str,    # capped at 300 chars
                        "score": float    # 0.0 - 1.0, higher = better
                    },
                    ...
                ],
                "query": str,
                "count": int
            }

        On error returns ``{"results": [], "error": "..."}``.
    """
    q = (query or "").strip()
    if not q:
        return json.dumps({"results": [], "error": "query is empty", "count": 0})

    try:
        k = int(top_k)
    except (TypeError, ValueError):
        k = 5
    k = max(_MIN_TOP_K, min(k, _MAX_TOP_K))

    svc = _get_search_service()

    try:
        await svc.initialize()
        req = SearchRequest(
            query=q,
            limit=k,
            min_score=0.0,
            use_reranking=True,
            include_summary=True,
        )
        resp = await svc.search(req)
    except Exception as exc:  # noqa: BLE001 — return error rather than raise
        logger.warning("search_articles skill failed: %s", exc)
        return json.dumps(
            {"results": [], "error": f"search failed: {exc}", "count": 0}
        )

    results = []
    for r in getattr(resp, "results", []) or []:
        # Build a snippet from summary first (already-distilled), falling
        # back to content preview. NEVER return raw body text — see
        # docs/notes/deepagents-api-surface.md §7.
        snippet_src = (
            getattr(r, "summary", None) or getattr(r, "content", None) or ""
        )
        snippet = (snippet_src or "")[:_SNIPPET_CHARS]
        # Score: prefer rerank score (more meaningful), fall back to similarity.
        score = (
            getattr(r, "relevance_score", None)
            if getattr(r, "relevance_score", None) is not None
            else getattr(r, "similarity_score", 0.0)
        )
        # ``id`` arrives as str-or-int depending on the row; coerce to int
        # for the agent contract since article IDs are always integers in
        # the SQLite schema.
        raw_id = getattr(r, "id", None)
        try:
            article_id = int(raw_id) if raw_id is not None else None
        except (TypeError, ValueError):
            article_id = raw_id

        results.append(
            {
                "article_id": article_id,
                "title": getattr(r, "title", "") or "",
                "source": getattr(r, "source", "") or "",
                "snippet": snippet,
                "score": float(score or 0.0),
            }
        )

    payload = {
        "results": results,
        "query": q,
        "count": len(results),
    }
    return json.dumps(payload, ensure_ascii=False)
