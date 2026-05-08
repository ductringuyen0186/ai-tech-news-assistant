"""
Unit Tests for SubagentPool (Mission 2, Milestone 3)
====================================================

Covers ``src/services/subagent_pool.py``:

* Happy path — start + done events fire, parsed dict returned.
* Best-effort failure (raised exception) — start + error events, returns
  ``None`` instead of re-raising.
* Best-effort failure (skill returns ``{"error": ...}`` JSON) — start +
  error events, returns ``None``.
* Concurrency cap — at most ``max_concurrent`` skills in flight at once.
* Wall-clock concurrency proof — 4 dispatches each sleeping 1s complete
  in ≤ 1.5s when ``max_concurrent=4`` (proves they actually run in
  parallel, not serially).
* StructuredTool dispatch — verifies the ``.ainvoke(args)`` branch of
  the flexible-callable contract.

All tests are pure-asyncio with no external services. They use a
sync ``lambda e: events.append(e)`` for ``on_event`` to mirror how the
M4 orchestrator will wire its event emitter.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List

import pytest
from langchain_core.tools import tool

from src.services.subagent_pool import SubagentPool


# ---------------------------------------------------------------------------- #
#  Helpers
# ---------------------------------------------------------------------------- #

def _make_collector() -> tuple[List[Dict[str, Any]], "callable"]:
    """Return (events_list, sync_callback) pair for collecting events."""
    events: List[Dict[str, Any]] = []
    return events, lambda ev: events.append(ev)


# ====================================================================== #
#  Happy path
# ====================================================================== #

class TestSubagentPoolHappyPath:
    """A successful dispatch fires start + done and returns the parsed dict."""

    @pytest.mark.asyncio
    async def test_dispatch_returns_parsed_dict(self):
        """skill_fn returns JSON; pool parses and returns a dict."""
        async def fake_skill(article_id: int) -> str:
            return json.dumps(
                {"article_id": article_id, "summary": "ok", "cache_hit": False}
            )

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        result = await pool.dispatch(
            fake_skill, {"article_id": 42}, on_event
        )

        assert result is not None
        assert result["article_id"] == 42
        assert result["summary"] == "ok"
        assert result["cache_hit"] is False

    @pytest.mark.asyncio
    async def test_dispatch_fires_start_then_done_events(self):
        """Exactly two events on success: start, then done with duration_ms."""
        async def fake_skill(article_id: int) -> str:
            return json.dumps({"article_id": article_id, "ok": True})

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        await pool.dispatch(fake_skill, {"article_id": 7}, on_event)

        assert len(events) == 2
        # start
        assert events[0]["type"] == "subagent"
        assert events[0]["data"] == "start"
        assert events[0]["skill"] == "fake_skill"
        assert events[0]["article_id"] == 7
        # done
        assert events[1]["type"] == "subagent"
        assert events[1]["data"] == "done"
        assert events[1]["skill"] == "fake_skill"
        assert events[1]["article_id"] == 7
        assert isinstance(events[1]["duration_ms"], int)
        assert events[1]["duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_dispatch_with_structured_tool_uses_ainvoke(self):
        """A LangChain @tool-decorated skill is dispatched via .ainvoke()."""
        @tool
        async def my_tool(article_id: int, focus_question: str = "") -> str:
            """Returns a JSON blob echoing the inputs."""
            return json.dumps(
                {
                    "article_id": article_id,
                    "focus_question": focus_question,
                    "echoed": True,
                }
            )

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        result = await pool.dispatch(
            my_tool,
            {"article_id": 99, "focus_question": "open source impact"},
            on_event,
        )

        assert result is not None
        assert result["article_id"] == 99
        assert result["focus_question"] == "open source impact"
        assert result["echoed"] is True
        # The StructuredTool's .name is what we should see in events.
        assert events[0]["skill"] == "my_tool"
        assert events[1]["skill"] == "my_tool"


# ====================================================================== #
#  Best-effort error handling
# ====================================================================== #

class TestSubagentPoolErrors:
    """Exceptions and JSON-error payloads are surfaced as events, not raised."""

    @pytest.mark.asyncio
    async def test_raised_exception_emits_error_and_returns_none(self):
        """skill_fn raises → start + error events, dispatch returns None."""
        async def boom(article_id: int) -> str:
            raise RuntimeError("ollama unavailable")

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        # Must NOT raise.
        result = await pool.dispatch(boom, {"article_id": 1}, on_event)

        assert result is None
        assert len(events) == 2
        assert events[0]["data"] == "start"
        assert events[1]["data"] == "error"
        assert events[1]["article_id"] == 1
        assert events[1]["skill"] == "boom"
        assert "ollama unavailable" in events[1]["message"]

    @pytest.mark.asyncio
    async def test_skill_returns_error_json_emits_error_event(self):
        """skill_fn returns {"error": ...} JSON → start + error events."""
        async def soft_fail(article_id: int) -> str:
            return json.dumps(
                {
                    "article_id": article_id,
                    "summary": "",
                    "cache_hit": False,
                    "error": "article body is empty",
                }
            )

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        result = await pool.dispatch(soft_fail, {"article_id": 5}, on_event)

        assert result is None
        assert len(events) == 2
        assert events[0]["data"] == "start"
        assert events[1]["data"] == "error"
        assert events[1]["article_id"] == 5
        assert events[1]["skill"] == "soft_fail"
        assert "article body is empty" in events[1]["message"]

    @pytest.mark.asyncio
    async def test_skill_returns_invalid_json_emits_error(self):
        """Non-JSON string → error event, not a hard raise."""
        async def bad_string(article_id: int) -> str:
            return "this is not JSON {{"

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        result = await pool.dispatch(bad_string, {"article_id": 8}, on_event)

        assert result is None
        assert len(events) == 2
        assert events[1]["data"] == "error"
        assert "invalid JSON" in events[1]["message"]


# ====================================================================== #
#  Concurrency cap (in-flight counter)
# ====================================================================== #

class TestSubagentPoolConcurrencyCap:
    """Pool enforces max_concurrent simultaneous in-flight dispatches."""

    @pytest.mark.asyncio
    async def test_max_in_flight_never_exceeds_cap(self):
        """10 dispatches × 100ms sleep — observed peak ≤ max_concurrent."""
        # Plain ints used as a sync counter — race conditions inside a
        # single asyncio loop are deterministic at the await boundary.
        state = {"in_flight": 0, "max_in_flight": 0}

        async def fake_skill(article_id: int) -> str:
            state["in_flight"] += 1
            if state["in_flight"] > state["max_in_flight"]:
                state["max_in_flight"] = state["in_flight"]
            try:
                await asyncio.sleep(0.1)
                return json.dumps({"article_id": article_id, "ok": True})
            finally:
                state["in_flight"] -= 1

        pool = SubagentPool(max_concurrent=3)
        events, on_event = _make_collector()

        tasks = [
            pool.dispatch(fake_skill, {"article_id": i}, on_event)
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        assert all(r is not None for r in results)
        assert state["in_flight"] == 0  # everything cleaned up
        assert state["max_in_flight"] <= 3, (
            f"Expected max in-flight <= 3, got {state['max_in_flight']}"
        )
        # Events: 10 starts + 10 dones = 20.
        assert len(events) == 20

    @pytest.mark.asyncio
    async def test_wall_clock_proves_parallel_execution(self):
        """4 dispatches × 1.0s sleep should finish in < 1.5s with cap=4.

        If the pool were serial, this would take >= 4s. The 1.5s ceiling
        leaves a 50% margin for asyncio.sleep precision on Windows.
        """
        async def slow_skill(article_id: int) -> str:
            await asyncio.sleep(1.0)
            return json.dumps({"article_id": article_id, "ok": True})

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        t0 = time.monotonic()
        tasks = [
            pool.dispatch(slow_skill, {"article_id": i}, on_event)
            for i in range(4)
        ]
        results = await asyncio.gather(*tasks)
        elapsed = time.monotonic() - t0

        assert all(r is not None for r in results)
        assert elapsed < 1.5, (
            f"Expected 4 parallel 1s dispatches < 1.5s, got {elapsed:.2f}s"
        )
        # Sanity: each dispatch's duration_ms should be ~1000.
        done_events = [e for e in events if e["data"] == "done"]
        assert len(done_events) == 4
        for e in done_events:
            assert e["duration_ms"] >= 900  # within sleep precision


# ====================================================================== #
#  Misc — constructor + property surface
# ====================================================================== #

class TestSubagentPoolMisc:
    @pytest.mark.asyncio
    async def test_default_max_concurrent_is_4(self):
        pool = SubagentPool()
        assert pool.max_concurrent == 4

    @pytest.mark.asyncio
    async def test_custom_max_concurrent(self):
        pool = SubagentPool(max_concurrent=7)
        assert pool.max_concurrent == 7

    @pytest.mark.asyncio
    async def test_zero_max_concurrent_rejected(self):
        with pytest.raises(ValueError):
            SubagentPool(max_concurrent=0)

    @pytest.mark.asyncio
    async def test_dispatch_with_no_article_id_works(self):
        """A skill that doesn't use article_id still gets dispatched cleanly."""
        async def search_like(query: str) -> str:
            return json.dumps({"results": [], "query": query, "count": 0})

        pool = SubagentPool(max_concurrent=4)
        events, on_event = _make_collector()

        result = await pool.dispatch(
            search_like, {"query": "rust"}, on_event
        )

        assert result is not None
        assert result["query"] == "rust"
        # article_id should be None in events when not provided.
        assert events[0]["article_id"] is None
        assert events[1]["article_id"] is None


# ====================================================================== #
#  Settings wiring
# ====================================================================== #

class TestSubagentPoolSettingsWiring:
    """Confirms the new ``max_concurrent_subagents`` field on Settings."""

    def test_settings_default_is_4(self):
        from src.core.config import Settings
        s = Settings()
        assert s.max_concurrent_subagents == 4

    def test_settings_env_override(self, monkeypatch):
        from src.core.config import Settings
        monkeypatch.setenv("MAX_CONCURRENT_SUBAGENTS", "12")
        s = Settings()
        assert s.max_concurrent_subagents == 12
