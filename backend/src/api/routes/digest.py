"""
Digest Route
============

Returns a daily-digest aggregation built from the SQLite store: top stories,
category breakdown, and trending topics. Powers the frontend's Digest tab.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ...core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/digest", tags=["Digest"])


@router.get("/")
async def get_daily_digest(top: int = 5) -> Dict[str, Any]:
    """
    Build a daily digest from the most recent articles in the DB.

    Shape matches the frontend's DigestView prop type: top stories, category
    breakdown (by source for now, since we don't have proper categories yet),
    and trending topics (most-frequent capitalised tokens in titles).
    """
    settings = get_settings()
    db_path = getattr(settings, "sqlite_database_path", "./news.db")

    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row

        # Top stories: most-recent N
        rows = con.execute(
            "SELECT id, title, source, summary, content, categories "
            "FROM articles WHERE is_archived = 0 "
            "ORDER BY created_at DESC LIMIT ?",
            (top,),
        ).fetchall()

        def _decode_categories(raw: Any) -> List[str]:
            """Parse the JSON-encoded categories TEXT column. Returns [] on
            null / malformed / non-list values so a single bad row never
            breaks the whole digest payload."""
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return []
            if isinstance(parsed, list):
                return [str(c) for c in parsed if c]
            return []

        top_stories: List[Dict[str, Any]] = [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "source": r["source"] or "Unknown",
                "summaryShort": (
                    r["summary"]
                    or (r["content"][:200] + "...")
                    if r["content"]
                    else ""
                ),
                # Pull category from the article's actual ``categories`` JSON
                # column instead of duplicating ``source``. The frontend
                # DigestView renders source + category as separate chips, so
                # using the source here produced "MIT Technology Review |
                # MIT Technology Review" twice on every story.
                "category": _decode_categories(r["categories"]),
            }
            for r in rows
        ]

        # Category breakdown: count by source (used as a proxy for category
        # until we have proper category extraction).
        breakdown_rows = con.execute(
            "SELECT source, COUNT(*) AS c FROM articles "
            "WHERE is_archived = 0 GROUP BY source ORDER BY c DESC"
        ).fetchall()
        category_breakdown: Dict[str, int] = {
            (r["source"] or "Unknown"): r["c"] for r in breakdown_rows
        }

        # Trending topics: most-frequent capitalised tokens in recent titles.
        title_rows = con.execute(
            "SELECT title FROM articles WHERE is_archived = 0 "
            "ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        token_counts: Counter = Counter()
        for tr in title_rows:
            for word in (tr["title"] or "").split():
                w = word.strip(",.:;'\"!?()[]")
                if len(w) >= 4 and w[0].isupper() and w.isalpha():
                    token_counts[w] += 1
        trending_topics = [
            {"id": f"trend-{i}", "title": term, "category": []}
            for i, (term, _) in enumerate(token_counts.most_common(5))
        ]

        con.close()

        return {
            "date": datetime.now(timezone.utc).isoformat(),
            "topStories": top_stories,
            "categoryBreakdown": category_breakdown,
            "trendingTopics": trending_topics,
        }
    except Exception as exc:
        logger.error("Failed to build digest: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Digest build failed: {exc}"
        )
