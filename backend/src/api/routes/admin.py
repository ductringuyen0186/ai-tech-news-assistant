"""
Admin Routes
============

Operator-facing endpoints for manual maintenance.

Currently exposes:
- ``POST /api/admin/retention/run?dry_run=<bool>`` -- trigger the retention
  service on demand. Useful for the first prod run (always do
  ``dry_run=true`` first), and as the hook used by the E2E test suite to
  verify retention without waiting for the daily cron.
- ``POST /api/admin/wipe?confirm=WIPE`` -- destructive: delete every row in
  ``articles``, ``embeddings``, ``embedding_metadata`` and
  ``article_categories``. Used by ``scripts/reset_data.sh`` to reset a
  deploy to a clean state. Refuses to do anything unless the literal
  string ``WIPE`` is passed; this is a deliberate, in-the-loop guardrail
  to make accidental hits via curl history or browser autocomplete
  obvious.

NOTE: There is no auth in this project. Until SSO lands, admin routes
should be firewalled at the reverse proxy / load balancer (e.g. require a
specific source IP or basic-auth in nginx). The daily cron itself runs
in-process and does not need an auth boundary.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from ...core.config import get_settings
from ...services.retention_service import RetentionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def _resolve_db_path(raw: str) -> str:
    """Strip the SQLAlchemy prefix the rest of the app uses."""
    if raw.startswith("sqlite:///"):
        return raw.replace("sqlite:///", "")
    return raw


@router.post("/retention/run")
async def run_retention(
    dry_run: bool = Query(
        default=False,
        description=(
            "If true, log/return what would be deleted without committing. "
            "Recommended for the first call against a fresh DB."
        ),
    ),
) -> Dict[str, Any]:
    """Trigger a retention pass on demand."""
    try:
        service = RetentionService()
        result = service.run(dry_run=dry_run)
        return {"status": "ok", "data": result.to_dict()}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Manual retention run failed")
        raise HTTPException(
            status_code=500,
            detail=f"Retention run failed: {exc}",
        )


@router.post("/wipe")
async def wipe_database(
    confirm: str = Query(
        default="",
        description=(
            "Must be the literal string 'WIPE' for the call to proceed. "
            "Anything else returns 400 without touching the DB."
        ),
    ),
) -> Dict[str, Any]:
    """Hard-delete every article and its dependent rows.

    Idempotent -- running on an already-empty DB returns zero counts and
    leaves tables in place. Tables that don't exist on this DB are
    skipped rather than crashing, so the call also works on a fresh
    install before the first ingest.
    """
    if confirm != "WIPE":
        raise HTTPException(
            status_code=400,
            detail=(
                "Refusing to wipe: query param 'confirm' must be the "
                "literal string 'WIPE'."
            ),
        )

    settings = get_settings()
    configured = settings.database_url or settings.sqlite_database_path
    db_path = _resolve_db_path(configured)

    counts: Dict[str, int] = {
        "articles": 0,
        "embeddings": 0,
        "embedding_metadata": 0,
        "article_categories": 0,
    }

    con = sqlite3.connect(db_path)
    try:
        # CASCADE on declared FKs (embedding_metadata -> embeddings)
        con.execute("PRAGMA foreign_keys = ON")

        # Order matters: dependents first, then articles. Each table is
        # wrapped in its own try so a missing table on a fresh DB is a
        # warning, not a 500. Mirrors the pattern in RetentionService.
        for table in (
            "embedding_metadata",
            "embeddings",
            "article_categories",
            "articles",
        ):
            try:
                cur = con.execute(f"DELETE FROM {table}")
                counts[table] = cur.rowcount or 0
            except sqlite3.OperationalError as exc:
                logger.warning("Skipping %s during wipe: %s", table, exc)

        con.commit()
        logger.warning(
            "Admin WIPE complete: articles=%d embeddings=%d "
            "embedding_metadata=%d article_categories=%d (db=%s)",
            counts["articles"],
            counts["embeddings"],
            counts["embedding_metadata"],
            counts["article_categories"],
            db_path,
        )
    except Exception:
        con.rollback()
        logger.exception("Admin WIPE failed; rolling back")
        raise HTTPException(status_code=500, detail="Wipe failed; see logs")
    finally:
        con.close()

    return {
        "status": "ok",
        "data": {
            "db_path": db_path,
            "deleted": counts,
            "total_deleted": sum(counts.values()),
        },
    }
