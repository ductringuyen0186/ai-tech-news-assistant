"""
Knowledge Graph Route
=====================

Serves the data behind the frontend's Knowledge Graph tab. Returns the top-N
named entities (by mention count) and the co-mention edges between them.

The shape is intentionally NOT wrapped in BaseResponse — the frontend reads
``response.nodes`` and ``response.edges`` directly. Keep it that way.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from ...core.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge-graph", tags=["KnowledgeGraph"])


# Hard cap on what we'll return regardless of what the caller asks for.
# The canvas in the frontend is fine up to ~150 nodes; past that the
# force-directed layout pegs the CPU.
MAX_LIMIT = 150
DEFAULT_LIMIT = 50

# Edge threshold: only include co-mentions seen in this many distinct
# articles. The issue asks for >= 2 — single-article co-mentions are usually
# the model spraying related entities at one story.
MIN_CO_MENTION_ARTICLES = 2


def _resolve_db_path() -> str:
    settings = get_settings()
    raw = getattr(settings, "sqlite_database_path", "./news.db")
    if isinstance(raw, str) and raw.startswith("sqlite:///"):
        raw = raw.replace("sqlite:///", "")
    return raw


def _ensure_entity_tables(conn: sqlite3.Connection) -> None:
    """No-op if tables already exist; otherwise create empty stubs.

    This means the endpoint stays 200-OK even before any extraction has
    run (returns ``{nodes: [], edges: []}``), which is what the frontend
    expects on a fresh DB.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            mention_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            position INTEGER,
            UNIQUE(article_id, entity_id)
        )
        """
    )


@router.get("/")
async def get_knowledge_graph(
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> Dict[str, Any]:
    """
    Return the top-``limit`` entities by mention count + their co-mention edges.

    Response shape (consumed directly by ``KnowledgeGraph.tsx``):

    ::

        {
          "nodes": [{"id": "1", "name": "OpenAI", "type": "company",
                     "mention_count": 14}, ...],
          "edges": [{"source": "1", "target": "7", "weight": 3}, ...],
          "total_entities": 42
        }

    ``nodes`` is sorted descending by ``mention_count``. ``edges`` only
    includes pairs co-mentioned in ``MIN_CO_MENTION_ARTICLES`` or more
    distinct articles, and only between nodes that made the top-N cut.
    """
    db_path = _resolve_db_path()

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_entity_tables(conn)

            entity_rows = conn.execute(
                "SELECT id, name, type, mention_count "
                "FROM entities "
                "WHERE mention_count > 0 "
                "ORDER BY mention_count DESC, name ASC "
                "LIMIT ?",
                (limit,),
            ).fetchall()

            total_entities = conn.execute(
                "SELECT COUNT(*) FROM entities WHERE mention_count > 0"
            ).fetchone()[0]

            nodes: List[Dict[str, Any]] = [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "type": row["type"],
                    "mention_count": int(row["mention_count"]),
                }
                for row in entity_rows
            ]

            edges: List[Dict[str, Any]] = []
            if len(nodes) >= 2:
                node_ids = [int(n["id"]) for n in nodes]
                # Build the IN clause safely with placeholders.
                placeholders = ",".join("?" * len(node_ids))
                # Self-join on entity_mentions to find co-mentions.
                # COUNT(DISTINCT article_id) is the edge weight.
                query = (
                    f"SELECT em1.entity_id AS a, em2.entity_id AS b, "
                    f"COUNT(DISTINCT em1.article_id) AS w "
                    f"FROM entity_mentions em1 "
                    f"JOIN entity_mentions em2 "
                    f"  ON em1.article_id = em2.article_id "
                    f"  AND em1.entity_id < em2.entity_id "
                    f"WHERE em1.entity_id IN ({placeholders}) "
                    f"  AND em2.entity_id IN ({placeholders}) "
                    f"GROUP BY em1.entity_id, em2.entity_id "
                    f"HAVING COUNT(DISTINCT em1.article_id) >= ? "
                    f"ORDER BY w DESC"
                )
                params = node_ids + node_ids + [MIN_CO_MENTION_ARTICLES]
                edge_rows = conn.execute(query, params).fetchall()
                edges = [
                    {
                        "source": str(row["a"]),
                        "target": str(row["b"]),
                        "weight": int(row["w"]),
                    }
                    for row in edge_rows
                ]

        return {
            "nodes": nodes,
            "edges": edges,
            "total_entities": int(total_entities),
        }
    except sqlite3.Error as exc:
        logger.error("Knowledge graph query failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Knowledge graph query failed: {exc}"
        )
