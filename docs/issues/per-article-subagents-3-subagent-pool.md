# [Feature] Build SubagentPool with max_concurrent=4 + per-article context isolation

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P0                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, agent, concurrency, subagents                                 |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 3 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
The architectural payoff of Mission 2 lives in M3: per-article reasoning happens in *isolated* subagent contexts, bounded by `max_concurrent = 4`. The orchestrator only ever sees article IDs + per-article summaries. This is what bounds context-window blowup AND unlocks concurrency.

## Description
**Today:** No SubagentPool exists. M1's run() does serial work in a single context.

**After this change:** A new `services/subagent_pool.py` exposes a `SubagentPool` class with:

```python
class SubagentPool:
    def __init__(self, max_concurrent: int = 4):
        self._sem = asyncio.Semaphore(max_concurrent)

    async def dispatch(
        self,
        skill_fn: Callable[..., Awaitable[Any]],
        args: dict,
        on_event: Callable[[dict], None],
    ) -> Any | None:
        """
        Run skill_fn(**args) under the semaphore. Emits subagent
        lifecycle events via on_event:
          - {"type": "subagent", "data": "start", "skill": ..., "article_id": ...}
          - {"type": "subagent", "data": "done",  "skill": ..., "article_id": ..., "duration_ms": ...}
          - {"type": "subagent", "data": "error", "skill": ..., "article_id": ..., "message": ...}

        Returns skill_fn's return value, or None on failure (best-effort).
        """
```

Each subagent invocation runs in an isolated context — implementation-wise, this means the skill_fn sees ONLY the args passed in (article_id, focus_question, etc.) and has no implicit access to the orchestrator's state. The skill_fn's prompt size is bounded by its own arguments, not by the size of the corpus.

`max_concurrent` is read from `settings.max_concurrent_subagents` (added to `core/config.py` in this milestone, default 4, env-var override `MAX_CONCURRENT_SUBAGENTS`).

## Acceptance criteria
- [ ] `backend/src/services/subagent_pool.py` exists with the `SubagentPool` class and `dispatch` async method
- [ ] `backend/src/core/config.py` adds `max_concurrent_subagents: int = 4` to the settings model with `MAX_CONCURRENT_SUBAGENTS` env override
- [ ] At most `max_concurrent` skill_fn calls are in flight simultaneously, verified by a unit test that:
  - Submits 10 dispatches each sleeping 100ms
  - Tracks an "in-flight counter" inside the skill_fn
  - Asserts the max in-flight value never exceeded `max_concurrent`
- [ ] Best-effort failure: a skill_fn raising an exception emits a `subagent: error` event but `dispatch` returns `None` rather than raising. Verified by unit test
- [ ] Wall-clock for 4 dispatches each sleeping 1s: ≤1.5s total (proves they actually run in parallel)
- [ ] On_event is called exactly twice on success (start + done) and exactly twice on failure (start + error)
- [ ] Per-call structured logs include `skill_name`, `article_id` (if present), `duration_ms`, `status`
- [ ] All 17 existing contract tests still pass

## Implementation notes
Files likely involved:
- `backend/src/services/subagent_pool.py` — NEW
- `backend/src/core/config.py` — add `max_concurrent_subagents` setting
- `backend/tests/unit/test_subagent_pool.py` — NEW

Gotchas:
- Use `asyncio.Semaphore`, not `asyncio.BoundedSemaphore` — the latter raises on over-release, which can mask bugs in best-effort code paths
- `time.monotonic()` for `duration_ms`, not `time.time()` (clock drift)
- Don't use `asyncio.gather(*tasks, return_exceptions=True)` here — the dispatch contract is per-call, not per-batch. The CALLER (M4's `AgenticResearchService`) decides how to gather
- Make sure `on_event` is a synchronous callback (the orchestrator's event-emit path is sync — avoid coroutine plumbing surprises)
- Per-article subagent isolation is enforced by the SHAPE of args — keep `args: dict` minimal: ONLY (article_id, focus_question) for `summarize_article`, ONLY (entity, depth) for `query_knowledge_graph`, etc.

## Out of scope
- M2's skills (already exist; M3 just dispatches them via the pool)
- M4's rewrite of `AgenticResearchService` (which IS the caller of this pool)
- Per-skill failure policy (flat best-effort)
- Subagent retry (one attempt per dispatch)

## Verification
- `pytest backend/tests/unit/test_subagent_pool.py -v` exits 0 with all 5+ tests green
- The 4-parallel-dispatch wall-clock test specifically asserts ≤1.5s for 4 × 1s sleeps
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend` exits 0

## Risks
- `asyncio.Semaphore` can deadlock if a task holds the semaphore and awaits its OWN release. Document in the docstring that `dispatch` should never recursively dispatch
- The "in-flight counter" test is fragile if `asyncio.sleep` clock resolution is too coarse — use 100ms sleeps and assert max-in-flight, not exact-in-flight
