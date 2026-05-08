"""
Integration tests for the Agentic Research SSE route (M2)
=========================================================

Covers the validation contract from
``docs/issues/agentic-research-2-sse-endpoint.md``:

1. ``test_sse_frame_shape`` -- POST returns ``text/event-stream`` and each
   ``data:`` frame is a discrete ``data: <json>\\n\\n`` block whose
   payload matches the AgentEvent shape; the terminal ``done`` event
   preserves its ``report`` key end-to-end.
2. ``test_token_streaming_emits_token_phase`` -- while synthesis is
   streaming, the client sees multiple ``type: "token"`` events before
   the final ``phase: "done"`` event.
3. ``test_keepalive_emitted_on_slow_event`` -- when no real event has
   been pending for the keepalive interval, a ``: keepalive\\n\\n``
   comment frame appears in the stream.
4. ``test_disconnect_cancels_inflight_generation`` -- when the client
   disconnects mid-run, the SSE generator's cancel/finally handler runs
   and the stub agent's ``except CancelledError`` branch fires.
5. ``test_second_concurrent_post_returns_429`` -- a second POST while
   one run is in flight returns HTTP 429 with the documented body.
6. ``test_inflight_gate_releases_on_completion`` -- after a normal run,
   the gate is released so a second POST succeeds.

Ollama is fully mocked: tests inject a fake agent service via a module-
level ``_build_service`` patch, so no live model is required.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from typing import Any, AsyncGenerator, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import research as research_route


# ---------------------------------------------------------------------- #
#  Helpers
# ---------------------------------------------------------------------- #


def _build_app() -> FastAPI:
    """Build a fresh FastAPI app mounting just the research router."""
    app = FastAPI()
    app.include_router(research_route.router, prefix="/api")
    return app


@pytest.fixture(autouse=True)
def _reset_inflight_gate():
    """Reset the single-in-flight gate before/after every test."""
    research_route._in_flight = False
    yield
    research_route._in_flight = False


def _parse_sse_blocks(body: bytes) -> List[bytes]:
    """Split a raw SSE body into discrete frames at ``\\n\\n`` boundaries."""
    blocks = body.split(b"\n\n")
    return [b for b in blocks if b.strip()]


def _data_payloads(blocks: List[bytes]) -> List[Dict[str, Any]]:
    """Extract JSON payloads from ``data:`` frames; ignore comment frames."""
    payloads: List[Dict[str, Any]] = []
    for blk in blocks:
        text = blk.decode("utf-8", "replace").strip()
        if text.startswith("data:"):
            json_text = text[len("data:"):].strip()
            try:
                payloads.append(json.loads(json_text))
            except json.JSONDecodeError:
                continue
    return payloads


class _StubAgent:
    """A fake :class:`AgenticResearchService` that yields canned events."""

    def __init__(
        self,
        events: List[Dict[str, Any]],
        *,
        per_event_delay: float = 0.0,
        on_cancel: Any = None,
    ):
        self._events = list(events)
        self._delay = per_event_delay
        self._on_cancel = on_cancel
        self.cancelled = False
        self.finally_ran = False

    async def run(self, question: str) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            for evt in self._events:
                if self._delay:
                    await asyncio.sleep(self._delay)
                yield evt
        except asyncio.CancelledError:
            self.cancelled = True
            if callable(self._on_cancel):
                self._on_cancel()
            raise
        except GeneratorExit:
            # ``aclose()`` raises GeneratorExit inside the generator;
            # treat it as a cancellation signal too so disconnect tests
            # can observe cleanup either way.
            self.cancelled = True
            if callable(self._on_cancel):
                self._on_cancel()
            raise
        finally:
            self.finally_ran = True


# ---------------------------------------------------------------------- #
#  Tests
# ---------------------------------------------------------------------- #


def test_sse_frame_shape(monkeypatch):
    """POST /api/research returns text/event-stream and well-shaped frames."""
    stub = _StubAgent(
        events=[
            {"type": "phase", "data": "Decomposing"},
            {"type": "phase", "data": "Searching (1/2)"},
            {"type": "phase", "data": "Synthesizing"},
            {"type": "token", "data": "## Summary\nHello "},
            {"type": "token", "data": "world.\n"},
            {
                "type": "phase",
                "data": "done",
                "report": "## Summary\nHello world.\n[1] x -- y (z)\n",
            },
        ]
    )
    monkeypatch.setattr(research_route, "_build_service", lambda: stub)

    app = _build_app()
    client = TestClient(app)
    with client.stream(
        "POST", "/api/research", json={"question": "anything"}
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = b"".join(resp.iter_bytes())

    blocks = _parse_sse_blocks(body)
    payloads = _data_payloads(blocks)

    assert [p["type"] for p in payloads] == [
        "phase", "phase", "phase", "token", "token", "phase",
    ]
    assert payloads[-1]["data"] == "done"
    assert "report" in payloads[-1]
    assert "[1]" in payloads[-1]["report"]

    for blk in blocks:
        text = blk.decode("utf-8", "replace")
        assert text.startswith("data:") or text.startswith(":"), text


def test_token_streaming_emits_token_phase(monkeypatch):
    """Multiple ``type: "token"`` events arrive before the terminal done."""
    stub = _StubAgent(
        events=[
            {"type": "phase", "data": "Synthesizing"},
            {"type": "token", "data": "alpha "},
            {"type": "token", "data": "beta "},
            {"type": "token", "data": "gamma"},
            {
                "type": "phase",
                "data": "done",
                "report": "alpha beta gamma\n[1] s\n",
            },
        ]
    )
    monkeypatch.setattr(research_route, "_build_service", lambda: stub)

    app = _build_app()
    client = TestClient(app)
    with client.stream(
        "POST", "/api/research", json={"question": "stream me"}
    ) as resp:
        body = b"".join(resp.iter_bytes())

    payloads = _data_payloads(_parse_sse_blocks(body))
    token_events = [p for p in payloads if p["type"] == "token"]
    assert len(token_events) >= 2, payloads
    last_idx = next(
        i for i, p in enumerate(payloads)
        if p["type"] == "phase" and p.get("data") == "done"
    )
    token_indices = [
        i for i, p in enumerate(payloads) if p["type"] == "token"
    ]
    assert all(i < last_idx for i in token_indices)


def test_keepalive_emitted_on_slow_event(monkeypatch):
    """A ``: keepalive\\n\\n`` comment frame appears when no event arrives."""
    stub = _StubAgent(
        events=[
            {"type": "phase", "data": "Decomposing"},
            {
                "type": "phase",
                "data": "done",
                "report": "ok\n[1] s\n",
            },
        ],
        per_event_delay=0.2,
    )
    monkeypatch.setattr(research_route, "_build_service", lambda: stub)
    monkeypatch.setattr(
        research_route, "KEEPALIVE_INTERVAL_SECONDS", 0.05
    )

    app = _build_app()
    client = TestClient(app)
    with client.stream(
        "POST", "/api/research", json={"question": "slow"}
    ) as resp:
        body = b"".join(resp.iter_bytes())

    assert b": keepalive\n\n" in body, body[:500]
    payloads = _data_payloads(_parse_sse_blocks(body))
    assert any(p["type"] == "phase" and p.get("data") == "done" for p in payloads)


def test_disconnect_cancels_inflight_generation():
    """Disconnect mid-run runs the agent's cancel/cleanup handler.

    We drive ``_stream_research`` directly with a fake Request that
    flips ``is_disconnected -> True`` after the first event arrives.
    This exercises the same finally / cancel logic that fires in
    production when a client closes the SSE connection, without
    depending on a real ASGI transport's TCP-close semantics.
    """
    cancel_observed = threading.Event()

    def _on_cancel():
        cancel_observed.set()

    stub = _StubAgent(
        events=[
            {"type": "phase", "data": "Decomposing"},
            {"type": "phase", "data": "Searching (1/1)"},
            {"type": "phase", "data": "Synthesizing"},
            *[{"type": "token", "data": "tk "} for _ in range(50)],
            {"type": "phase", "data": "done", "report": "ok\n[1] s\n"},
        ],
        per_event_delay=0.05,
        on_cancel=_on_cancel,
    )

    class _FakeRequest:
        """Minimal Request stand-in: flips disconnected after N polls."""

        def __init__(self, flip_after: int = 1):
            self._polls = 0
            self._flip_after = flip_after

        async def is_disconnected(self) -> bool:
            self._polls += 1
            return self._polls > self._flip_after

    async def _drive() -> None:
        agen = stub.run("dummy")
        req = _FakeRequest(flip_after=1)
        # Iterate a few frames then expect the generator to short-circuit
        # because is_disconnected returns True on its second poll.
        out = research_route._stream_research(req, agen)
        try:
            count = 0
            async for _frame in out:
                count += 1
                if count > 100:  # safety
                    break
        finally:
            await out.aclose()
        # Allow the scheduled cancellation to settle.
        for _ in range(20):
            if stub.cancelled or cancel_observed.is_set():
                return
            await asyncio.sleep(0.05)

    asyncio.run(_drive())

    assert stub.cancelled or cancel_observed.is_set(), (
        "expected agent generator to receive CancelledError / GeneratorExit "
        "on simulated disconnect"
    )
    assert stub.finally_ran, "agent generator finally block should always run"


def test_second_concurrent_post_returns_429(monkeypatch):
    """A second POST while a run is in flight returns HTTP 429."""
    monkeypatch.setattr(
        research_route, "_build_service",
        lambda: _StubAgent(events=[]),
    )

    research_route._in_flight = True

    app = _build_app()
    client = TestClient(app)
    resp = client.post("/api/research", json={"question": "second"})
    assert resp.status_code == 429
    body = resp.json()
    assert body == {"detail": "Another research run is in flight"}


def test_inflight_gate_releases_on_completion(monkeypatch):
    """After a run completes, the gate is released so the next POST works."""
    stub = _StubAgent(
        events=[
            {"type": "phase", "data": "done", "report": "x\n[1] y\n"},
        ]
    )
    monkeypatch.setattr(research_route, "_build_service", lambda: stub)

    app = _build_app()
    client = TestClient(app)
    with client.stream(
        "POST", "/api/research", json={"question": "one"}
    ) as resp:
        b"".join(resp.iter_bytes())

    assert research_route._in_flight is False
    with client.stream(
        "POST", "/api/research", json={"question": "two"}
    ) as resp:
        assert resp.status_code == 200
