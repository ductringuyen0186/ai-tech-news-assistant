"""
SubagentPool — concurrency-bounded per-article skill dispatcher
===============================================================

This module implements Mission 2, Milestone 3: a hand-rolled subagent pool
that gates per-article reasoning at ``max_concurrent`` (default 4) using a
single ``asyncio.Semaphore``. It lives OUTSIDE the deepagents middleware
(see ``docs/notes/deepagents-api-surface.md`` §6 — Option B) so:

* The semaphore is in our code, not buried in middleware we'd have to
  reach into.
* The orchestrator's "no raw body text in the outer prompt" guarantee is
  enforced by *what we pass to skill_fn*, not by deepagents internals.
* SSE event shapes (``subagent: start / done / error``) are emitted
  directly — no translation layer.

Design contract
---------------
``dispatch(skill_fn, args, on_event)`` is a per-call primitive. The
CALLER (M4's ``AgenticResearchService``) is responsible for batching
multiple dispatches via ``asyncio.gather`` or similar — this class does
NOT batch. Per-call lifecycle:

1. Acquire the semaphore (blocks until a slot is free).
2. Emit ``{"type": "subagent", "data": "start", ...}``.
3. ``await skill_fn.ainvoke(args)`` if the callable looks like a
   LangChain ``StructuredTool``; otherwise ``await skill_fn(**args)``.
4. Parse the JSON return value (skills emit JSON strings — see M2's
   contract). If the parsed dict has an ``"error"`` key, treat it as a
   best-effort failure: emit ``subagent: error``, return ``None``.
5. Otherwise emit ``subagent: done`` with ``duration_ms`` and return
   the parsed dict.
6. Any unexpected exception → emit ``subagent: error``, return ``None``.
7. Always release the semaphore.

The pool is fire-and-forget at the per-call level: ``dispatch`` never
raises. This is the M3 "best-effort" contract — a single bad article
must not poison the whole orchestrator run.

Per-article context isolation is enforced by the SHAPE of ``args``: the
caller must pass ONLY the minimal fields each skill expects (e.g.
``{"article_id": 42, "focus_question": "..."}`` for ``summarize_article``).
The pool does NOT inject any implicit context — what the skill sees is
exactly what the caller put in ``args``.

Risks documented:

* ``asyncio.Semaphore`` can deadlock if a task holds the semaphore and
  awaits its own release. Do NOT recursively dispatch from inside a
  skill.
* The pool uses ``time.monotonic()`` for ``duration_ms`` (clock-drift
  resilient). Wall-clock timing in tests should use the same.

See ``docs/issues/per-article-subagents-3-subagent-pool.md`` for the
acceptance criteria this module satisfies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional


logger = logging.getLogger(__name__)


# Type alias: the on_event callback is SYNC. The orchestrator's event-emit
# path (an async generator that yields dicts) wraps appends in a sync
# closure to avoid coroutine-plumbing surprises. Tests use a plain
# ``lambda e: events.append(e)``.
EventCallback = Callable[[Dict[str, Any]], None]


class SubagentPool:
    """Concurrency-bounded dispatcher for per-article agent skills.

    Args:
        max_concurrent: Maximum number of skill_fn invocations in flight
            at once. Defaults to 4 (matches
            ``settings.max_concurrent_subagents``).

    Example::

        pool = SubagentPool(max_concurrent=4)
        events: list[dict] = []
        result = await pool.dispatch(
            summarize_article,
            {"article_id": 42, "focus_question": None},
            on_event=lambda e: events.append(e),
        )
        # `events` now has 2 entries: start + done (or start + error)
        # `result` is the parsed-JSON dict, or None on failure.
    """

    def __init__(self, max_concurrent: int = 4) -> None:
        if max_concurrent < 1:
            raise ValueError(
                f"max_concurrent must be >= 1, got {max_concurrent}"
            )
        # Plain Semaphore (NOT BoundedSemaphore) — over-release would mask
        # bugs in best-effort code paths rather than help debugging.
        self._sem: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent

    @property
    def max_concurrent(self) -> int:
        """The configured concurrency cap (read-only)."""
        return self._max_concurrent

    async def dispatch(
        self,
        skill_fn: Callable[..., Awaitable[Any]],
        args: Dict[str, Any],
        on_event: EventCallback,
    ) -> Optional[Dict[str, Any]]:
        """Run ``skill_fn`` under the semaphore and emit lifecycle events.

        ``skill_fn`` is invoked flexibly:

        * If it has an ``ainvoke`` method (LangChain ``StructuredTool``
          via ``@tool``), call ``await skill_fn.ainvoke(args)``.
        * Otherwise treat it as a plain async function and call
          ``await skill_fn(**args)``.

        The skill is expected to return a JSON string (Mission 2 M2
        contract). The string is parsed; if the resulting dict contains
        an ``"error"`` key, it is treated as a best-effort failure and a
        ``subagent: error`` event is emitted. Otherwise a
        ``subagent: done`` event is emitted with ``duration_ms``.

        Args:
            skill_fn: The skill to dispatch (a ``StructuredTool`` or a
                plain async callable).
            args: Keyword arguments to pass to the skill. Must be
                JSON-serialisable (article_id, focus_question, etc.).
                The pool does NOT add any implicit context — per-article
                isolation is enforced by what's in this dict.
            on_event: SYNC callback invoked with each lifecycle event.
                Called exactly twice per dispatch: once with ``start``,
                once with either ``done`` or ``error``. Exceptions in
                this callback are NOT caught — the pool assumes the
                caller's emitter is well-behaved.

        Returns:
            The parsed-JSON dict on success (the skill's return value
            after ``json.loads``), or ``None`` on any failure mode
            (raised exception, JSON parse error, ``"error"`` key).

        Notes:
            * Uses ``time.monotonic()`` for ``duration_ms`` — robust
              against wall-clock drift.
            * Never raises. Best-effort: a single bad dispatch must
              not poison the orchestrator's batch.
            * Do NOT recursively dispatch from inside a skill — the
              shared semaphore can deadlock.
        """
        skill_name = _skill_name(skill_fn)
        article_id = args.get("article_id") if isinstance(args, dict) else None

        async with self._sem:
            t0 = time.monotonic()

            # ---- start event -------------------------------------------------
            on_event(
                {
                    "type": "subagent",
                    "data": "start",
                    "skill": skill_name,
                    "article_id": article_id,
                }
            )
            logger.info(
                "subagent.dispatch.start skill=%s article_id=%s",
                skill_name,
                article_id,
            )

            # ---- invoke ------------------------------------------------------
            try:
                raw = await _invoke(skill_fn, args)
            except Exception as exc:  # noqa: BLE001 — best-effort, must not raise
                duration_ms = int((time.monotonic() - t0) * 1000)
                message = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "subagent.dispatch.error skill=%s article_id=%s "
                    "duration_ms=%d status=error message=%s",
                    skill_name,
                    article_id,
                    duration_ms,
                    message,
                )
                on_event(
                    {
                        "type": "subagent",
                        "data": "error",
                        "skill": skill_name,
                        "article_id": article_id,
                        "message": message,
                    }
                )
                return None

            # ---- parse return value -----------------------------------------
            parsed: Optional[Dict[str, Any]] = None
            if isinstance(raw, str):
                try:
                    decoded = json.loads(raw)
                except (TypeError, ValueError) as exc:
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    message = f"invalid JSON from skill: {exc}"
                    logger.warning(
                        "subagent.dispatch.error skill=%s article_id=%s "
                        "duration_ms=%d status=error message=%s",
                        skill_name,
                        article_id,
                        duration_ms,
                        message,
                    )
                    on_event(
                        {
                            "type": "subagent",
                            "data": "error",
                            "skill": skill_name,
                            "article_id": article_id,
                            "message": message,
                        }
                    )
                    return None
                if isinstance(decoded, dict):
                    parsed = decoded
                else:
                    # Non-dict JSON (list / scalar) — treat as success but
                    # wrap so the caller still gets a dict.
                    parsed = {"result": decoded}
            elif isinstance(raw, dict):
                # A skill that returned a dict directly (not the M2
                # contract, but defensive).
                parsed = raw
            else:
                # Anything else — wrap it so the caller's contract is
                # preserved.
                parsed = {"result": raw}

            # ---- check for skill-emitted error key --------------------------
            if "error" in parsed:
                duration_ms = int((time.monotonic() - t0) * 1000)
                message = str(parsed.get("error"))
                logger.warning(
                    "subagent.dispatch.error skill=%s article_id=%s "
                    "duration_ms=%d status=error message=%s",
                    skill_name,
                    article_id,
                    duration_ms,
                    message,
                )
                on_event(
                    {
                        "type": "subagent",
                        "data": "error",
                        "skill": skill_name,
                        "article_id": article_id,
                        "message": message,
                    }
                )
                return None

            # ---- success ----------------------------------------------------
            duration_ms = int((time.monotonic() - t0) * 1000)
            cache_hit = parsed.get("cache_hit") if isinstance(parsed, dict) else None
            logger.info(
                "subagent.dispatch.done skill=%s article_id=%s "
                "duration_ms=%d status=ok cache_hit=%s",
                skill_name,
                article_id,
                duration_ms,
                cache_hit,
            )
            on_event(
                {
                    "type": "subagent",
                    "data": "done",
                    "skill": skill_name,
                    "article_id": article_id,
                    "duration_ms": duration_ms,
                }
            )
            return parsed


# ---------------------------------------------------------------------------- #
#  Helpers
# ---------------------------------------------------------------------------- #

def _skill_name(skill_fn: Any) -> str:
    """Best-effort name extraction for logs + events.

    LangChain ``StructuredTool`` exposes ``.name``; plain async functions
    expose ``__name__``. Fall back to ``repr`` so we never KeyError on a
    missing attribute.
    """
    name = getattr(skill_fn, "name", None)
    if isinstance(name, str) and name:
        return name
    name = getattr(skill_fn, "__name__", None)
    if isinstance(name, str) and name:
        return name
    return repr(skill_fn)


async def _invoke(skill_fn: Any, args: Dict[str, Any]) -> Any:
    """Call ``skill_fn`` flexibly — StructuredTool first, then plain async.

    Both call shapes are valid in this codebase:

    * ``@tool``-decorated functions become ``StructuredTool`` instances
      and are dispatched via ``.ainvoke({"arg": value})``.
    * Plain async helpers (used inside tests + future internal calls)
      are dispatched via ``skill_fn(**args)``.
    """
    ainvoke = getattr(skill_fn, "ainvoke", None)
    if callable(ainvoke):
        return await ainvoke(args)
    return await skill_fn(**args)
