"""Probe the search_articles skill to find good queries for the live tests.

Run from backend/:
    python scripts/probe_search_for_live_tests.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.agent_skills import search_articles  # noqa: E402


PROBES = [
    ("Kodiak AI funding", 5),
    ("Bumble dating swipe", 5),
    ("Tome book tracker shutdown", 5),
    ("Disney super app", 5),
    ("OpenAI", 10),
    ("OpenAI lawsuit", 10),
    ("AI news today", 25),
    ("AI startups and funding", 25),
]


async def main():
    for query, k in PROBES:
        try:
            out = await search_articles.ainvoke({"query": query, "top_k": k})
        except Exception as exc:
            print(f"==== {query!r} -> ERROR: {exc}")
            continue
        d = json.loads(out)
        results = d.get("results") or []
        print(f"==== {query!r} (top_k={k}) -> count={d.get('count')}")
        for r in results[:8]:
            title = (r.get("title") or "")[:70]
            print(f"  id={r['article_id']} score={r['score']:.3f} title={title}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
