# [Refactor] Replace AgenticResearchService with deepagents-backed agent loop

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Refactor                                                               |
| Priority       | P0                                                                     |
| Estimate       | L                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, agent, deepagents, breaking-internal                          |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 4 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
With the spike (M1) decided, skills (M2) implemented, and SubagentPool (M3) ready, M4 is the headline change: replace M1's hand-rolled `AgenticResearchService` with a deepagents-backed agent loop (or, if M1 said NO-GO, a custom `Agent` class using the SubagentPool + SkillRegistry directly). The public SSE event shape is preserved; new `subagent` events are added.

## Description
**Today:** `services/agentic_research_service.py` is ~700 lines of hand-rolled decompose/search/synthesize logic. Every article's content goes into one big synthesis prompt.

**After this change:** The service is rewritten end-to-end:

1. The orchestrator is a deepagents `Agent` (or custom equivalent) with the 4 skills from M2 registered as tools
2. The agent's prompt receives ONLY the user's question and a list of `{article_id, title, source}` tuples (NOT raw bodies)
3. When the agent decides to summarize an article, it calls `summarize_article(article_id, focus_question)` via SubagentPool; the subagent returns just the summary string
4. The orchestrator aggregates per-article summaries and synthesizes the final report
5. The async generator `run(question)` yields:
   - The same outer phases as M1 (`Decomposing → Searching (i/N) → Synthesizing → Done`)
   - PLUS new `subagent` events for every dispatch (start/done/error)
   - PLUS the existing `token` events during synthesis (the orchestrator's synthesis stream)
   - PLUS the existing `done` event with the canonical report on `event["report"]`

The `_ensure_sources_section` guard rail from M1 is preserved (or its equivalent is reimplemented inside the new agent's synthesis post-process).

## Acceptance criteria
- [ ] `backend/src/services/agentic_research_service.py` is rewritten using deepagents (or fallback architecture per M1 decision)
- [ ] The orchestrator's prompt to the LLM contains article IDs + summaries but NEVER raw article body text. Asserted via a fixture that captures the prompt and runs `assert "<full body marker>" not in prompt`
- [ ] `await`-consuming `service.run("...")` yields, in order: one `phase: "Decomposing"`, ≥1 `phase: "Searching (i/N)"`, ≥1 `subagent: start`, matching `subagent: done` (or `error`), one `phase: "Synthesizing"`, multiple `phase: "token"`, exactly one `phase: "done"` with `report` populated
- [ ] At most `max_concurrent_subagents` `subagent: start` events are unmatched by `done`/`error` at any moment (max-in-flight cap honored)
- [ ] Best-effort failures: forcing one `summarize_article` call to throw produces a `subagent: error` event but the run still completes with a `phase: "done"` event
- [ ] The final report contains ≥1 `[N]` citation marker AND ≥1 `## Sources Used` entry (citation guard rail preserved)
- [ ] All 16 unit tests in `test_agentic_research_service.py` are rewritten for the new implementation; all pass
- [ ] All 6 integration tests in `test_research_sse.py` continue to pass (M1's outer SSE shape is preserved as backward-compat)
- [ ] One new integration test asserts that ≥1 `subagent: start` and matching `subagent: done` appear in a typical run
- [ ] All 17 contract tests still green

## Implementation notes
Files likely involved:
- `backend/src/services/agentic_research_service.py` — REWRITTEN
- `backend/src/models/article.py` — extend `AgentEvent` (allow `type = "subagent"` with `skill`, `article_id`, `duration_ms`, `message` fields)
- `backend/src/api/routes/research.py` — minor: nothing should change because the route is shape-agnostic (it just `json.dumps(event)`s every yielded dict). VERIFY this is true.
- `backend/tests/unit/test_agentic_research_service.py` — significant rewrite
- `backend/tests/integration/test_research_sse.py` — add 1-2 new tests for subagent events
- `backend/scripts/spike_deepagents.py` — can be archived or deleted; M4 supersedes it

Gotchas:
- The deepagents Agent loop is likely synchronous-with-callbacks at its core. Wrap it in an async generator using `asyncio.Queue` or similar so it streams events to the SSE route
- The orchestrator's prompt SIZE assertion is the canary: write a unit test that runs the agent against 50 articles and asserts the orchestrator's prompt is < N tokens (specific N decided after the spike)
- Subagent events fire from inside SubagentPool.dispatch via `on_event` callback. Wire that to `yield` the event up the async generator chain
- The `token` events during synthesis come from the orchestrator's own LLM call, not from subagents. Don't conflate
- Backward compatibility: the `done` event still has `event["report"]` (NOT `event["data"]`) — preserved from M1's choice; downstream M3+M4 frontend code depends on this

## Out of scope
- Frontend changes (M5 owns those)
- Ingestion-time summarization migration (M6 owns that)
- New skills beyond the 4 from M2

## Verification
- `pytest backend/tests/unit/test_agentic_research_service.py backend/tests/integration/test_research_sse.py -v` exits 0
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend` exits 0 with 17/17
- Manual smoke (optional): a curl POST to `/api/research` with a real question produces a stream that includes `data: {"type": "subagent", ...}` lines

## Risks
- The deepagents Agent's tool-call decision-making with `gpt-oss:20b` may be unreliable. If it consistently picks the wrong skill or generates invalid JSON, fall back to the M1-style hand-rolled JSON-output prompts (this is the M1 spike's escape hatch)
- The orchestrator may want to call `summarize_article` for every search result, blowing up the subagent dispatch count. Cap the orchestrator's article list at top_K=8 in the prompt to bound the work
- The async-generator wrapping around deepagents' sync-callback core is the main complexity — allocate buffer in M4's estimate for it
