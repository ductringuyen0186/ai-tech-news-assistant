"""
Unit Tests for Agent Skills (Mission 2, Milestone 2)
====================================================

Covers the four ``@tool``-decorated agent skills under
``src/services/agent_skills/``:

* ``search_articles``        -- happy path + error path
* ``summarize_article``      -- happy path, cache hit, cache miss + write-back
* ``extract_entities``       -- happy path
* ``query_knowledge_graph``  -- happy path with depth=1 over a fixture graph

All tests mock the underlying services and SQLite (via a temp DB) so the
suite runs without a live backend or Ollama.
"""

from __future__ import annotations

import importlib
import json
import sqlite3
import tempfile
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.article import ArticleSummary
from src.models.search import SearchResponse, SearchResultItem


# The package ``__init__.py`` rebinds the four tool functions onto
# ``src.services.agent_skills`` itself, which shadows the submodule names
# (``src.services.agent_skills.search_articles`` becomes the
# ``StructuredTool`` rather than the module). To reach module-level
# globals (the ``_search_service`` / ``_repository`` singletons we want
# to swap for mocks) we go through ``importlib.import_module``, which
# bypasses the package-level rebinding and returns the actual module.
def _import_skill_module(name: str):
    return importlib.import_module(f"src.services.agent_skills.{name}")


# ---------------------------------------------------------------------- #
#  Helpers — temp DB + tool invocation
# ---------------------------------------------------------------------- #

def _new_temp_db() -> str:
    """Return the path to a fresh temp SQLite file (caller must unlink)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


def _seed_articles_table(db_path: str, rows: List[Dict[str, Any]]) -> None:
    """Create + populate the ``articles`` table for the cache-hit tests.

    Mirrors the bootstrap inside :class:`ArticleRepository`.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                author TEXT,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                categories TEXT,
                metadata TEXT,
                is_archived BOOLEAN DEFAULT FALSE,
                view_count INTEGER DEFAULT 0,
                embedding_generated BOOLEAN DEFAULT FALSE,
                summary_generated BOOLEAN DEFAULT FALSE,
                image_url TEXT
            )
            """
        )
        for r in rows:
            conn.execute(
                "INSERT INTO articles (id, title, url, content, summary, "
                "source, summary_generated) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    r["id"],
                    r["title"],
                    r["url"],
                    r.get("content"),
                    r.get("summary"),
                    r.get("source", "test"),
                    1 if r.get("summary") else 0,
                ),
            )


def _seed_entity_graph(db_path: str) -> None:
    """Create the entity tables and seed a tiny co-mention graph.

    Two articles, three entities. Entities A and B co-mention in
    article 1, A and C co-mention in article 2. The seed-from-A walk
    therefore yields edges A-B and A-C with weight 1 each.
    """
    with sqlite3.connect(db_path) as conn:
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
        # Entities
        conn.execute(
            "INSERT INTO entities (id, name, type, mention_count) "
            "VALUES (1, 'OpenAI', 'company', 2)"
        )
        conn.execute(
            "INSERT INTO entities (id, name, type, mention_count) "
            "VALUES (2, 'Sam Altman', 'person', 1)"
        )
        conn.execute(
            "INSERT INTO entities (id, name, type, mention_count) "
            "VALUES (3, 'Microsoft', 'company', 1)"
        )
        # Mentions: article 1 mentions OpenAI + Sam Altman;
        # article 2 mentions OpenAI + Microsoft.
        conn.execute(
            "INSERT INTO entity_mentions (article_id, entity_id, position) "
            "VALUES (1, 1, 0), (1, 2, 1), (2, 1, 0), (2, 3, 1)"
        )


# ---------------------------------------------------------------------- #
#  Per-test reset of the module-level singletons inside each skill
# ---------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _reset_skill_singletons():
    """Each test gets a fresh service singleton so prior mocks don't bleed."""
    sa_mod = _import_skill_module("search_articles")
    sa_mod._search_service = None
    su_mod = _import_skill_module("summarize_article")
    su_mod._repository = None
    su_mod._summarizer = None
    ee_mod = _import_skill_module("extract_entities")
    ee_mod._extractor = None
    yield


# ====================================================================== #
#  search_articles
# ====================================================================== #

class TestSearchArticlesSkill:
    """Happy + error paths for ``search_articles``."""

    @pytest.mark.asyncio
    async def test_search_articles_happy_path(self):
        """Wraps SearchService.search and returns the documented shape."""
        from src.services.agent_skills import search_articles
        sa_mod = _import_skill_module("search_articles")

        # Mock SearchService entirely
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock()
        mock_svc.search = AsyncMock(
            return_value=SearchResponse(
                query="OpenAI",
                results=[
                    SearchResultItem(
                        id="42",
                        title="OpenAI ships GPT-5",
                        url="https://example.com/a",
                        source="techcrunch",
                        published_at=datetime.now(timezone.utc),
                        content="raw body should NOT leak to orchestrator",
                        summary="OpenAI shipped GPT-5 today with new reasoning capabilities.",
                        categories=["AI"],
                        keywords=["GPT-5", "OpenAI"],
                        similarity_score=0.92,
                        relevance_score=0.95,
                    )
                ],
                total_results=1,
                execution_time_ms=12.0,
                filters_applied={},
            )
        )
        sa_mod._search_service = mock_svc

        raw = await search_articles.ainvoke(
            {"query": "OpenAI", "top_k": 3}
        )
        payload = json.loads(raw)

        assert payload["count"] == 1
        assert payload["query"] == "OpenAI"
        hit = payload["results"][0]
        assert hit["article_id"] == 42
        assert hit["title"] == "OpenAI ships GPT-5"
        assert hit["source"] == "techcrunch"
        # snippet should come from summary, not raw content
        assert "OpenAI shipped GPT-5" in hit["snippet"]
        # score should pick rerank score over similarity
        assert hit["score"] == pytest.approx(0.95)
        # The mock should have been called with top_k clamped/forwarded.
        mock_svc.search.assert_awaited_once()
        req_arg = mock_svc.search.await_args.args[0]
        assert req_arg.query == "OpenAI"
        assert req_arg.limit == 3

    @pytest.mark.asyncio
    async def test_search_articles_empty_query_returns_error(self):
        """Empty query is rejected without hitting SearchService."""
        from src.services.agent_skills import search_articles

        raw = await search_articles.ainvoke({"query": "   "})
        payload = json.loads(raw)
        assert payload["results"] == []
        assert payload["count"] == 0
        assert "empty" in payload.get("error", "").lower()


# ====================================================================== #
#  summarize_article — happy / cache-hit / cache-miss-writeback
# ====================================================================== #

class TestSummarizeArticleSkill:
    """``summarize_article`` honours the cache-reuse contract from M2.M2."""

    @pytest.mark.asyncio
    async def test_summarize_happy_path_no_cache(self):
        """Article has body but no stored summary, no focus_question:
        LLM is called and result is written back."""
        from src.services.agent_skills import summarize_article
        su_mod = _import_skill_module("summarize_article")
        from src.repositories.article_repository import ArticleRepository

        db_path = _new_temp_db()
        try:
            _seed_articles_table(
                db_path,
                [
                    {
                        "id": 1,
                        "title": "T",
                        "url": "https://x/1",
                        "content": "Long article body about new AI lab opening.",
                        "summary": None,
                    }
                ],
            )
            su_mod._repository = ArticleRepository(db_path=db_path)

            # Mock summarization service
            mock_summ = MagicMock()
            mock_summ.model = "llama3.2:1b"
            mock_summ.summarize_content = AsyncMock(
                return_value=ArticleSummary(
                    id=0,
                    title="",
                    source="",
                    url="",
                    summary="A new AI lab opened today.",
                    word_count=6,
                    original_length=44,
                    summary_length=24,
                    compression_ratio=0.5,
                    processing_time=0.1,
                    model_used="llama3.2:1b",
                )
            )
            su_mod._summarizer = mock_summ

            raw = await summarize_article.ainvoke({"article_id": 1})
            payload = json.loads(raw)

            assert payload["article_id"] == 1
            assert payload["cache_hit"] is False
            assert payload["summary"] == "A new AI lab opened today."
            mock_summ.summarize_content.assert_awaited_once()
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass

    @pytest.mark.asyncio
    async def test_summarize_cache_hit_returns_without_llm(self):
        """When a stored summary exists and focus_question is None, the
        LLM must NOT be called."""
        from src.services.agent_skills import summarize_article
        su_mod = _import_skill_module("summarize_article")
        from src.repositories.article_repository import ArticleRepository

        db_path = _new_temp_db()
        try:
            _seed_articles_table(
                db_path,
                [
                    {
                        "id": 7,
                        "title": "T",
                        "url": "https://x/7",
                        "content": "Body",
                        "summary": "Cached summary text from a prior run.",
                    }
                ],
            )
            su_mod._repository = ArticleRepository(db_path=db_path)

            mock_summ = MagicMock()
            mock_summ.model = "llama3.2:1b"
            mock_summ.summarize_content = AsyncMock()  # MUST NOT BE CALLED
            su_mod._summarizer = mock_summ

            raw = await summarize_article.ainvoke({"article_id": 7})
            payload = json.loads(raw)

            assert payload["article_id"] == 7
            assert payload["cache_hit"] is True
            assert payload["summary"] == "Cached summary text from a prior run."
            mock_summ.summarize_content.assert_not_awaited()
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass

    @pytest.mark.asyncio
    async def test_summarize_cache_miss_writes_back_to_db(self):
        """Cache miss -> LLM call -> write-back to articles.summary."""
        from src.services.agent_skills import summarize_article
        su_mod = _import_skill_module("summarize_article")
        from src.repositories.article_repository import ArticleRepository

        db_path = _new_temp_db()
        try:
            _seed_articles_table(
                db_path,
                [
                    {
                        "id": 99,
                        "title": "T",
                        "url": "https://x/99",
                        "content": "Article body that needs summarising.",
                        "summary": None,
                    }
                ],
            )
            su_mod._repository = ArticleRepository(db_path=db_path)

            generated = "Newly generated summary."
            mock_summ = MagicMock()
            mock_summ.model = "llama3.2:1b"
            mock_summ.summarize_content = AsyncMock(
                return_value=ArticleSummary(
                    id=0, title="", source="", url="",
                    summary=generated, word_count=3, original_length=37,
                    summary_length=24, compression_ratio=0.65,
                    processing_time=0.1, model_used="llama3.2:1b",
                )
            )
            su_mod._summarizer = mock_summ

            raw = await summarize_article.ainvoke({"article_id": 99})
            payload = json.loads(raw)

            assert payload["cache_hit"] is False
            assert payload["summary"] == generated

            # Verify write-back actually happened in the DB
            with sqlite3.connect(db_path) as conn:
                row = conn.execute(
                    "SELECT summary FROM articles WHERE id = 99"
                ).fetchone()
            assert row is not None
            assert row[0] == generated, (
                f"expected write-back of generated summary; got {row[0]!r}"
            )
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass

    @pytest.mark.asyncio
    async def test_summarize_focus_question_bypasses_cache(self):
        """When focus_question is set, the LLM is called even if a
        stored summary exists, and the result is NOT written back."""
        from src.services.agent_skills import summarize_article
        su_mod = _import_skill_module("summarize_article")
        from src.repositories.article_repository import ArticleRepository

        db_path = _new_temp_db()
        try:
            _seed_articles_table(
                db_path,
                [
                    {
                        "id": 5,
                        "title": "T",
                        "url": "https://x/5",
                        "content": "Body",
                        "summary": "Cached neutral summary.",
                    }
                ],
            )
            su_mod._repository = ArticleRepository(db_path=db_path)

            mock_summ = MagicMock()
            mock_summ.model = "llama3.2:1b"
            mock_summ.summarize_content = AsyncMock(
                return_value=ArticleSummary(
                    id=0, title="", source="", url="",
                    summary="Focus-tailored summary.",
                    word_count=3, original_length=4, summary_length=23,
                    compression_ratio=5.7, processing_time=0.1,
                    model_used="llama3.2:1b",
                )
            )
            su_mod._summarizer = mock_summ

            raw = await summarize_article.ainvoke(
                {"article_id": 5, "focus_question": "How does this affect devs?"}
            )
            payload = json.loads(raw)

            assert payload["cache_hit"] is False
            assert payload["summary"] == "Focus-tailored summary."
            mock_summ.summarize_content.assert_awaited_once()

            # Cached summary should NOT have been overwritten — the cache
            # only stores neutral summaries.
            with sqlite3.connect(db_path) as conn:
                row = conn.execute(
                    "SELECT summary FROM articles WHERE id = 5"
                ).fetchone()
            assert row[0] == "Cached neutral summary."
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass


# ====================================================================== #
#  extract_entities
# ====================================================================== #

class TestExtractEntitiesSkill:

    @pytest.mark.asyncio
    async def test_extract_entities_happy_path(self):
        """Wraps EntityExtractionService.process_article and returns shape."""
        from src.services.agent_skills import extract_entities
        ee_mod = _import_skill_module("extract_entities")

        db_path = _new_temp_db()
        try:
            _seed_entity_graph(db_path)

            # Mock EntityExtractionService — process_article succeeds and
            # we already pre-seeded the graph so the post-extract read
            # finds entities under article_id=1.
            mock_extractor = MagicMock()
            mock_extractor.db_path = db_path
            mock_extractor.process_article = AsyncMock(return_value=2)
            ee_mod._extractor = mock_extractor

            raw = await extract_entities.ainvoke({"article_id": 1})
            payload = json.loads(raw)

            assert payload["article_id"] == 1
            assert payload["entity_count"] == 2
            names = {e["name"] for e in payload["entities"]}
            assert "OpenAI" in names
            assert "Sam Altman" in names
            mock_extractor.process_article.assert_awaited_once_with(1)
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass


# ====================================================================== #
#  query_knowledge_graph
# ====================================================================== #

class TestQueryKnowledgeGraphSkill:

    @pytest.mark.asyncio
    async def test_query_knowledge_graph_depth1_returns_edges(self):
        """depth=1 over a seeded graph returns >=1 edge from the seed
        entity to a co-mentioned entity."""
        from src.services.agent_skills import query_knowledge_graph
        qkg_mod = _import_skill_module("query_knowledge_graph")

        db_path = _new_temp_db()
        try:
            _seed_entity_graph(db_path)

            # Patch the path resolver to point at our temp DB.
            with patch.object(qkg_mod, "_resolve_db_path", return_value=db_path):
                raw = await query_knowledge_graph.ainvoke(
                    {"entity_or_topic": "OpenAI", "depth": 1}
                )
            payload = json.loads(raw)

            assert payload["seed"] == "OpenAI"
            assert "error" not in payload, f"unexpected error: {payload.get('error')}"
            # Seed + at least one neighbour
            assert len(payload["nodes"]) >= 2
            assert len(payload["edges"]) >= 1

            # Seed flag is correct
            seed_nodes = [n for n in payload["nodes"] if n["is_seed"]]
            assert len(seed_nodes) == 1
            assert seed_nodes[0]["name"] == "OpenAI"

            # Edges connect the seed (id=1) to neighbours
            seed_id = seed_nodes[0]["id"]
            for edge in payload["edges"]:
                # Edge keys are unordered (min, max), so the seed should
                # be on one end of every edge for depth=1.
                assert seed_id in (edge["source"], edge["target"]), (
                    f"depth=1 edge does not touch seed: {edge}"
                )
                assert edge["weight"] >= 1
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass

    @pytest.mark.asyncio
    async def test_query_knowledge_graph_unknown_entity_returns_empty(self):
        """A seed that doesn't exist in the graph returns empty payload
        with an error message — not a raised exception."""
        from src.services.agent_skills import query_knowledge_graph
        qkg_mod = _import_skill_module("query_knowledge_graph")

        db_path = _new_temp_db()
        try:
            _seed_entity_graph(db_path)
            with patch.object(qkg_mod, "_resolve_db_path", return_value=db_path):
                raw = await query_knowledge_graph.ainvoke(
                    {"entity_or_topic": "NonExistentCorp"}
                )
            payload = json.loads(raw)
            assert payload["nodes"] == []
            assert payload["edges"] == []
            assert "no entity found" in payload.get("error", "").lower()
        finally:
            try:
                os.unlink(db_path)
            except OSError:
                pass


# ====================================================================== #
#  Package-level smoke
# ====================================================================== #

class TestAgentSkillsPackage:
    """The package exports the four documented skills."""

    def test_package_exports_four_skills(self):
        from src.services import agent_skills

        for name in (
            "search_articles",
            "summarize_article",
            "extract_entities",
            "query_knowledge_graph",
        ):
            assert hasattr(agent_skills, name), f"missing export: {name}"
            tool_obj = getattr(agent_skills, name)
            # @tool-decorated objects expose .name and .ainvoke.
            assert hasattr(tool_obj, "ainvoke"), (
                f"{name} does not look like a LangChain tool"
            )
            assert hasattr(tool_obj, "name")
