"""
Unit Tests — Saved Research (M3.M5)
====================================

Covers the SavedResearchRepository CRUD surface and the 100-row cap
policy enforced at the repository level via ``count`` + ``delete_oldest``.

The repository ``_ensure_table_exists`` runs in the constructor, so every
test instantiates a fresh repo against a temp DB and verifies the table
is created against both a fresh file and an existing file.
"""

from __future__ import annotations

import time

import pytest

from src.repositories.saved_research_repository import (
    MAX_SAVED_ROWS,
    SavedResearchRepository,
)


# --------------------------------------------------------------------- #
#  Fixtures
# --------------------------------------------------------------------- #


@pytest.fixture
def repo(temp_db_path) -> SavedResearchRepository:
    """Fresh repository bound to a temporary on-disk SQLite file."""
    return SavedResearchRepository(db_path=temp_db_path)


# --------------------------------------------------------------------- #
#  Tests
# --------------------------------------------------------------------- #


def test_create_returns_id(repo: SavedResearchRepository):
    """``create`` returns an int id for the new row."""
    new_id = repo.create(
        question="What is the state of AI chips?",
        report_md="# Report\n\nBody.",
        sources=[{"n": 1, "title": "A", "source": "x", "url": "https://a"}],
    )
    assert isinstance(new_id, int)
    assert new_id > 0


def test_list_orders_by_created_at_desc(repo: SavedResearchRepository):
    """``list_all`` returns rows newest-first.

    We sleep 1.1s between inserts so the SQLite ``CURRENT_TIMESTAMP``
    (whole-second precision) yields distinct timestamps; the id
    tie-break secondary sort means we don't strictly require this, but
    it nails down the primary contract (created_at DESC) too.
    """
    id_a = repo.create("Q1", "# A", [])
    time.sleep(1.1)
    id_b = repo.create("Q2", "# B", [])
    time.sleep(1.1)
    id_c = repo.create("Q3", "# C", [])

    rows = repo.list_all()
    ids_in_order = [r[0] for r in rows]
    # Newest first: id_c, id_b, id_a.
    assert ids_in_order == [id_c, id_b, id_a]


def test_get_by_id_returns_record(repo: SavedResearchRepository):
    """``get_by_id`` returns the full record with parsed sources."""
    sources = [
        {"n": 1, "title": "Source One", "source": "techcrunch.com"},
        {"n": 2, "title": "Source Two", "source": "verge.com"},
    ]
    new_id = repo.create("Question?", "# Markdown body", sources)

    record = repo.get_by_id(new_id)
    assert record is not None
    assert record["id"] == new_id
    assert record["question"] == "Question?"
    assert record["report_md"] == "# Markdown body"
    assert record["sources"] == sources
    assert isinstance(record["created_at"], str)
    assert record["created_at"]  # non-empty


def test_get_by_id_returns_none_when_missing(repo: SavedResearchRepository):
    """``get_by_id`` returns ``None`` for an unknown id, not raises."""
    assert repo.get_by_id(99999) is None


def test_delete_removes_row(repo: SavedResearchRepository):
    """``delete_by_id`` returns True and removes the row.

    A second delete on the same id returns False.
    """
    new_id = repo.create("Q", "# R", [])
    assert repo.get_by_id(new_id) is not None

    assert repo.delete_by_id(new_id) is True
    assert repo.get_by_id(new_id) is None

    # Idempotency: deleting again returns False.
    assert repo.delete_by_id(new_id) is False


def test_create_caps_at_100_rows(repo: SavedResearchRepository):
    """When the table is at the cap, calling create should evict the
    oldest row to make room for the new one.

    The route handler is the layer responsible for invoking
    ``delete_oldest`` — this test exercises the same code-path end-to-end
    via the repository surface to ensure the cap is enforceable.
    """
    # Backdate-insert MAX_SAVED_ROWS rows. To avoid sleeping 100 seconds
    # we insert them with explicit ascending created_at values via raw
    # SQL so the eviction order is deterministic.
    import sqlite3

    with sqlite3.connect(repo.db_path) as conn:
        for i in range(MAX_SAVED_ROWS):
            ts = f"2024-01-01 00:{i // 60:02d}:{i % 60:02d}"
            conn.execute(
                "INSERT INTO saved_research (question, report_md, sources_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (f"Q{i}", f"# R{i}", "[]", ts),
            )
        conn.commit()

    assert repo.count() == MAX_SAVED_ROWS
    # The oldest is the one we backdated to 00:00:00 with question "Q0".
    rows_asc = repo.list_all(limit=MAX_SAVED_ROWS)
    oldest_id = rows_asc[-1][0]
    oldest_question = rows_asc[-1][1]
    assert oldest_question == "Q0"

    # Simulate the route handler's cap policy.
    if repo.count() >= MAX_SAVED_ROWS:
        evicted = repo.delete_oldest()
        assert evicted is True

    new_id = repo.create("New question", "# new", [])
    assert repo.count() == MAX_SAVED_ROWS

    # The oldest row is gone; the new row is present.
    assert repo.get_by_id(oldest_id) is None
    assert repo.get_by_id(new_id) is not None
    assert repo.get_by_id(new_id)["question"] == "New question"


def test_table_works_on_existing_db_file(temp_db_path):
    """Instantiating the repo a second time against the same file
    does not raise — the IF NOT EXISTS guard handles existing tables.

    This is the explicit ``works on fresh AND existing news.db`` check
    called out in the M3.M5 acceptance criteria.
    """
    repo1 = SavedResearchRepository(db_path=temp_db_path)
    id1 = repo1.create("Q1", "# A", [{"n": 1}])

    # Re-instantiating against the same on-disk DB must not fail or
    # destroy existing rows.
    repo2 = SavedResearchRepository(db_path=temp_db_path)
    record = repo2.get_by_id(id1)
    assert record is not None
    assert record["question"] == "Q1"
    assert record["sources"] == [{"n": 1}]


def test_empty_sources_round_trip(repo: SavedResearchRepository):
    """Empty list and None for sources both round-trip as ``[]``."""
    id_none = repo.create("Q-none", "# R", None)
    id_empty = repo.create("Q-empty", "# R", [])

    rec_none = repo.get_by_id(id_none)
    rec_empty = repo.get_by_id(id_empty)
    assert rec_none is not None and rec_empty is not None
    assert rec_none["sources"] == []
    assert rec_empty["sources"] == []
