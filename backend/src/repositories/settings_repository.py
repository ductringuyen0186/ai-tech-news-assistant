"""
Settings Repository
==================

Data access for the single-row ``settings`` table. Mirrors the lightweight
``sqlite3``-direct style used by ``digest.py`` and ``article_repository.py``
rather than going through SQLAlchemy sessions, since:

* the running backend doesn't call ``Base.metadata.create_all()`` at startup
* this is a one-row, one-table CRUD with no relationships
* the repository auto-creates the table on first touch via
  ``CREATE TABLE IF NOT EXISTS``, matching how ``ArticleRepository`` bootstraps

The SQLAlchemy ``Settings`` model in ``database.models`` describes the same
shape and is included for typing / future migrations, but isn't used here at
runtime.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional


SETTINGS_ROW_ID = 1  # Singleton primary key — there is only ever one row.


class SettingsRepository:
    """Repository for the singleton ``settings`` row."""

    def __init__(self, db_path: str):
        # Mirror ArticleRepository: accept a SQLAlchemy URL or a bare path.
        if db_path.startswith("sqlite:///"):
            self.db_path = db_path.replace("sqlite:///", "")
        else:
            self.db_path = db_path
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    categories TEXT,
                    view_mode TEXT NOT NULL DEFAULT 'detailed',
                    show_trending_only INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get(self) -> Optional[Dict[str, Any]]:
        """
        Return the singleton settings row as a dict, or ``None`` if no row
        has been written yet (caller is expected to fall back to defaults).
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT id, categories, view_mode, show_trending_only, updated_at "
                "FROM settings WHERE id = ?",
                (SETTINGS_ROW_ID,),
            ).fetchone()
            if not row:
                return None

            categories = None
            if row["categories"]:
                try:
                    categories = json.loads(row["categories"])
                except (json.JSONDecodeError, TypeError):
                    categories = None

            return {
                "categories": categories,
                "view_mode": row["view_mode"],
                "show_trending_only": bool(row["show_trending_only"]),
                "updated_at": row["updated_at"],
            }

    def upsert(
        self,
        *,
        categories: Optional[list] = None,
        view_mode: Optional[str] = None,
        show_trending_only: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Upsert the singleton row. Fields left as ``None`` keep their current
        (or default) value. Returns the post-write state as a dict.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            existing = conn.execute(
                "SELECT id, categories, view_mode, show_trending_only "
                "FROM settings WHERE id = ?",
                (SETTINGS_ROW_ID,),
            ).fetchone()

            now_iso = datetime.now(timezone.utc).isoformat()

            if existing is None:
                # First write — insert with whatever was supplied; falling
                # back to None for categories so GET-with-no-row defaults
                # logic remains the *only* place defaults live.
                cats_json = (
                    json.dumps(categories) if categories is not None else None
                )
                vm = view_mode if view_mode is not None else "detailed"
                trending = (
                    1 if (show_trending_only is True) else 0
                )
                conn.execute(
                    "INSERT INTO settings (id, categories, view_mode, "
                    "show_trending_only, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (SETTINGS_ROW_ID, cats_json, vm, trending, now_iso),
                )
            else:
                # Merge: keep existing values for any field not supplied.
                if categories is not None:
                    cats_json = json.dumps(categories)
                else:
                    cats_json = existing["categories"]
                vm = view_mode if view_mode is not None else existing["view_mode"]
                if show_trending_only is None:
                    trending = existing["show_trending_only"]
                else:
                    trending = 1 if show_trending_only else 0
                conn.execute(
                    "UPDATE settings SET categories = ?, view_mode = ?, "
                    "show_trending_only = ?, updated_at = ? WHERE id = ?",
                    (cats_json, vm, trending, now_iso, SETTINGS_ROW_ID),
                )
            conn.commit()

        result = self.get()
        # ``get`` always returns a row here since we just wrote one.
        assert result is not None
        return result
