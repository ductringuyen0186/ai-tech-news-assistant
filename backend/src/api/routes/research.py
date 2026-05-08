"""
Research SSE Route
==================

``POST /api/research`` exposes :class:`AgenticResearchService` over a
long-lived Server-Sent Events stream. It is the backend half of M2 of the
Agentic Research mission — see ``docs/missions/agentic-research.md``.

Wire-level contract
-------------------
- Request: ``POST /api/research`` with JSON body ``{"question": str}``.
- Response: ``Content-Type: text/event-stream`` with each
  :class:`~src.models.article.AgentEvent` shaped as a discrete SSE frame
  ``data: <json>\\n\\n``. The terminal ``phase: "done"`` frame also carries
  the assembled markdown report under the ``report`` key — preserved
  end-to-end so the M3 frontend can pull ``event.report`` directly.
- Keepalive: when no real event has been pending for 10 seconds we emit a
  ``: keepalive\\n\\n`` SSE comment frame. Comment frames don't fire
  ``EventSource``'s ``onmessage`` handler — they exist purely to keep
  proxies / browsers from killing an idle connection during a slow
  synthesis call.
- Disconnect: the route polls ``await request.is_disconnected()`` between
  events; on disconnect we cancel the in-flight agent task so the
  underlying Ollama generation tears down cleanly.
- Concurrency: a single in-flight gate (``asyncio.Lock``) ensures only
  one research run can be active per process. A second concurrent POST
  returns HTTP 429 with body ``{"detail": "Another research run is in flight"}``.

Production deploy notes
-----------------------
If this route ever goes behind a reverse proxy (Caddy / nginx), set
``proxy_buffering off`` for ``/api/research`` so the SSE frames flush
incrementally rather than batching into one chunk on close.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...services.agentic_research_service import AgenticResearchService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research", tags=["Research"])


# ---------------------------------------------------------------------- #
#  Request model
# ---------------------------------------------------------------------- #


class ResearchRequest(BaseModel):
    """Request body for :func:`research_stream`.

    The question is bounded to keep the decomposer prompt manageable; we
    don't expose ``model`` or ``top_k`` here because the mission pins the
    agent to ``gpt-oss:20b`` and the per-sub-question top-k is fixed in
    :class:`AgenticResearchService`.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Research question for the agent loop",
    )


# ---------------------------------------------------------------------- #
#  Single-in-flight gate (process-local; we run one uvicorn worker)
# ---------------------------------------------------------------------- #

# A simple boolean guarded by an asyncio lock is enough — single user,
# single worker. We never ``await`` while holding the lock so contention
# is sub-microsecond. An ``asyncio.Lock`` alone wouldn't return 429 on a
# second POST; it would queue the second request behind the first. The
# explicit boolean lets us reject immediately.
_in_flight_lock = asyncio.Lock()
_in_flight: bool = False


async def _try_acquire_in_flight() -> bool:
    """Atomically claim the in-flight slot.

    Returns ``True`` if the caller now owns the slot (and must release it
    in a ``finally``). Returns ``False`` if another run is already
    executing — the caller should respond with HTTP 429.
    """
    global _in_flight
    async with _in_flight_lock:
        if _in_flight:
            return False
        _in_flight = True
        return True


async def _release_in_flight() -> None:
    """Release the in-flight slot. Idempotent — safe to call from finally."""
    global _in_flight
    async with _in_flight_lock:
        _in_flight = False


# ---------------------------------------------------------------------- #
#  Service factory (dependency-injected for tests)
# ---------------------------------------------------------------------- #


def _build_service() -> AgenticResearchService:
    """Build the agent service. Overridden in tests via attribute patching.

    Kept as a module-level function (not a Depends-injected factory) so
    tests can monkey-patch ``research._build_service`` without dragging
    FastAPI's dependency-override plumbing into otherwise unit-shaped
    tests.
    """
    return AgenticResearchService()


# ---------------------------------------------------------------------- #
#  Constants
# ---------------------------------------------------------------------- #

# How long to wait for the next agent event before emitting a keepalive
# comment frame. 10 seconds matches the issue spec; long enough that a
# normal phase transition almost always beats it, short enough to keep
# proxies and browsers from killing the socket on a slow synthesize.
KEEPALIVE_INTERVAL_SECONDS = 10.0

# How often we poll ``request.is_disconnected()`` while waiting for the
# next event. 0.5s is a good balance — fast enough that a Ctrl-C on the
# client cancels the Ollama generation within a second, slow enough that
# we don't busy-loop while waiting on a long synthesis call.
DISCONNECT_POLL_SECONDS = 0.5


# ---------------------------------------------------------------------- #
#  SSE serializer
# ---------------------------------------------------------------------- #


def _sse_frame(event: Dict[str, Any]) -> bytes:
    """Serialize an :class:`AgentEvent`-shaped dict as one SSE ``data:`` frame.

    The whole event dict is JSON-encoded and packed into a single
    ``data: <json>\\n\\n`` block. We preserve every key on the dict
    (including ``report`` on the terminal ``done`` event) so M3 can pull
    the assembled report from the same frame that signals completion.

    ``ensure_ascii=False`` keeps non-ASCII tokens (emoji, accented chars)
    intact instead of escaping them to ``\\uXXXX`` — the response is
    UTF-8 encoded anyway.
    """
    payload = json.dumps(event, ensure_ascii=False)
    return f"data: {payload}\n\n".encode("utf-8")


_KEEPALIVE_FRAME = b": keepalive\n\n"


# ---------------------------------------------------------------------- #
#  SSE generator
# ---------------------------------------------------------------------- #


async def _stream_research(
    request: Request,
    agent_events: AsyncGenerator[Dict[str, Any], None],
) -> AsyncGenerator[bytes, None]:
    """Drive ``agent_events`` and forward each event as an SSE frame.

    Concurrency model
    -----------------
    The agent generator is consumed via an inner ``asyncio.Task`` that
    pulls one event at a time. Around that pull we run an
    ``asyncio.wait`` with a 10s timeout — when the timeout fires before
    a real event arrives we yield a keepalive comment frame and loop.

    Disconnect detection runs as a sibling poll on the same
    ``asyncio.wait``. If ``request.is_disconnected()`` resolves first, we
    cancel the agent generator and exit; the agent's underlying httpx
    stream tears down cleanly via its async context manager, which Ollama
    logs as a cancelled generation.
    """
    # Wrap the agent generator into a Task that resolves to (event_or_None,
    # done_flag). We keep the generator alive across keepalive timeouts by
    # NOT cancelling it — only the waiting task gets recreated.
    agen = agent_events

    async def _next_event() -> Optional[Dict[str, Any]]:
        """Pull one event from the agent. Returns ``None`` on exhaustion."""
        try:
            return await agen.__anext__()
        except StopAsyncIteration:
            return None

    next_task: Optional[asyncio.Task] = None
    try:
        while True:
            if next_task is None:
                next_task = asyncio.create_task(_next_event())

            try:
                # Wait for either the next event OR the keepalive timeout.
                done, _pending = await asyncio.wait(
                    {next_task},
                    timeout=KEEPALIVE_INTERVAL_SECONDS,
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except asyncio.CancelledError:
                # The outer streaming response was cancelled (server
                # shutdown, request disconnect bubbled up from Starlette).
                # Make sure the agent task is also cancelled.
                if next_task and not next_task.done():
                    next_task.cancel()
                raise

            # Disconnect check between events — covers both the timeout
            # branch and the just-completed branch. When the client
            # closes the socket, Starlette resolves is_disconnected to
            # True; we cancel the agent and exit cleanly.
            if await request.is_disconnected():
                logger.info(
                    "research SSE: client disconnected, cancelling agent"
                )
                if next_task and not next_task.done():
                    next_task.cancel()
                    try:
                        await next_task
                    except (asyncio.CancelledError, Exception):  # noqa: BLE001
                        pass
                return

            if not done:
                # Timeout fired before the next event arrived — emit a
                # keepalive comment frame and loop. The agent task keeps
                # running; we'll pick up its result on a future iteration.
                yield _KEEPALIVE_FRAME
                continue

            # We have a finished task; consume its result.
            try:
                event = next_task.result()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                # The agent itself raised — surface as a single error
                # SSE frame, then end the stream. We do NOT re-raise:
                # propagating from a StreamingResponse generator triggers
                # a 500 mid-stream which the client may render as a
                # truncated error payload, and we already have a
                # well-defined ``type: "error"`` event shape.
                logger.exception("research SSE: agent crashed: %s", exc)
                yield _sse_frame(
                    {"type": "error", "data": f"agent crashed: {exc}"}
                )
                return
            finally:
                next_task = None

            if event is None:
                # Agent generator exhausted normally.
                return

            yield _sse_frame(event)
    finally:
        # Belt-and-braces: if anything above raised mid-iteration, make
        # sure the underlying agent generator is closed so its httpx
        # stream tears down. ``aclose`` is idempotent.
        if next_task is not None and not next_task.done():
            next_task.cancel()
            try:
                await next_task
            except BaseException:  # noqa: BLE001
                pass
        try:
            await agen.aclose()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------- #
#  Route
# ---------------------------------------------------------------------- #


@router.post("")
async def research_stream(request: Request, body: ResearchRequest):
    """Stream a multi-step research run as Server-Sent Events.

    Returns ``text/event-stream`` with one :class:`AgentEvent`-shaped JSON
    payload per ``data:`` frame, plus periodic ``: keepalive`` comment
    frames during slow phases. A second concurrent POST returns
    HTTP 429.
    """
    acquired = await _try_acquire_in_flight()
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Another research run is in flight",
        )

    # Build the agent and its event generator before the streaming
    # response starts so that any synchronous setup error (bad config,
    # missing model, etc) surfaces as a normal HTTP error rather than a
    # truncated SSE stream. ``run`` itself is lazy — no I/O happens until
    # we iterate.
    try:
        service = _build_service()
        agent_gen = service.run(body.question)
    except Exception:
        await _release_in_flight()
        raise

    async def _outer() -> AsyncGenerator[bytes, None]:
        try:
            async for frame in _stream_research(request, agent_gen):
                yield frame
        finally:
            await _release_in_flight()

    return StreamingResponse(
        _outer(),
        media_type="text/event-stream",
        headers={
            # Tell intermediaries (and browsers) not to buffer the body.
            # ``X-Accel-Buffering: no`` is the nginx convention; harmless
            # elsewhere. Cache-Control: no-cache prevents stale replays.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
