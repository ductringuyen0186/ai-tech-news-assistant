# Mission: Per-article subagents + deepagents SDK

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Status         | **Phase 1 complete — awaiting Phase 2 approval**               |
| Owner          | duc (orchestrator)                                             |
| Created        | 2026-05-08                                                     |
| Target ship    | 2026-05-15 (~7 days)                                           |
| Design context | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |
| PRD            | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) |
| Skill          | [missions](../../.claude/skills/missions/SKILL.md) |

This mission replaces M1's `AgenticResearchService` with a deepagents-backed agent loop that **isolates per-article reasoning into subagent contexts**, capped at `max_concurrent = 4`. Four skills (`search_articles`, `summarize_article` with cache reuse, `extract_entities`, `query_knowledge_graph`) are exposed via deepagents tool registry.

It is broken into 6 milestones, each with its own ticketable issue and validation contract. The orchestrator (this Claude session) will spawn one worker subagent per milestone serially, then run scrutiny + user-testing validators in parallel after each worker hands off, retrying up to 3 times per milestone before surfacing to the user.

---

## Milestones (in order)

### M1 — deepagents spike + adopt/fallback decision *(M, ~1.5 days)*
- **Issue:** [docs/issues/per-article-subagents-1-deepagents-spike.md](../issues/per-article-subagents-1-deepagents-spike.md)
- **Goal:** Install deepagents, build a "hello world" agent with one skill, decide GO/NO-GO. Locks the path for M2-M6.
- **Validation contract (top 3):**
  1. `deepagents` (or langchain-deepagents) installed and pinned in `backend/requirements.txt`
  2. `backend/scripts/spike_deepagents.py` runs successfully against live Ollama, prints tool calls + final output
  3. `docs/notes/deepagents-api-surface.md` exists with an explicit GO/NO-GO verdict citing ≥3 specific compatibility checks

### M2 — 4 skills implementation *(M, ~1 day)*
- **Issue:** [docs/issues/per-article-subagents-2-skills.md](../issues/per-article-subagents-2-skills.md)
- **Goal:** Implement `search_articles`, `summarize_article` (with cache reuse), `extract_entities`, `query_knowledge_graph` as deepagents tools (or fallback custom skills).
- **Validation contract (top 3):**
  1. Each skill exists in `services/agent_skills/` with clear schema
  2. `summarize_article` returns `cache_hit=True` when `articles.summary` exists and `focus_question is None`; generates and writes back otherwise
  3. New unit tests cover all 4 skills + cache hit/miss; 17 contract tests stay green

### M3 — SubagentPool + per-article context isolation *(M, ~1.5 days)*
- **Issue:** [docs/issues/per-article-subagents-3-subagent-pool.md](../issues/per-article-subagents-3-subagent-pool.md)
- **Goal:** Build `SubagentPool` with `asyncio.Semaphore(4)`. Per-article subagent contexts: each only sees its own article + the user's question.
- **Validation contract (top 3):**
  1. At most `max_concurrent` skill_fn calls in flight simultaneously (verified by counter test)
  2. Best-effort failure: skill_fn raise emits `subagent: error` event; dispatch returns None instead of raising
  3. Wall-clock for 4 parallel dispatches × 1s sleep ≤ 1.5s (proves concurrency)

### M4 — Rewrite AgenticResearchService *(L, ~1 day)*
- **Issue:** [docs/issues/per-article-subagents-4-rewrite-agent.md](../issues/per-article-subagents-4-rewrite-agent.md)
- **Goal:** Replace M1 internals with deepagents Agent + skills + SubagentPool. Preserve outer SSE shape; add `subagent` events.
- **Validation contract (top 3):**
  1. Orchestrator's prompt contains article IDs + summaries but NEVER raw body text (asserted via prompt-inspection fixture)
  2. SSE stream emits `subagent: start` / `done` (or `error`) events for every dispatch; max-in-flight cap honored
  3. Final report has ≥1 `[N]` citation + `## Sources Used` section (citation guard rail preserved)

### M5 — Frontend Subagents panel *(M, ~1 day)*
- **Issue:** [docs/issues/per-article-subagents-5-frontend-panel.md](../issues/per-article-subagents-5-frontend-panel.md)
- **Goal:** Render per-article subagent activity in the UI. Auto-expanding collapsible panel.
- **Validation contract (top 3):**
  1. Panel renders ≥1 row when subagent events arrive (asserted via Playwright)
  2. Existing 5-test `research.spec.ts` still green after mock SSE bodies updated
  3. 8-category UX rubric still passes; no console errors

### M6 — Ingestion migration + final validation *(M, ~1 day)*
- **Issue:** [docs/issues/per-article-subagents-6-ingestion-and-validation.md](../issues/per-article-subagents-6-ingestion-and-validation.md)
- **Goal:** Migrate ingestion summarization to use the `summarize_article` skill. Update live test. Run full E2E.
- **Validation contract (top 3):**
  1. `SummarizationOrchestrator` calls `agent_skills.summarize_article` (gated by `USE_AGENT_SKILL_SUMMARIZATION` flag, default True)
  2. Smoke test (`smoke_ingest_via_skill.py`) ingests + summarizes a small feed, every article has non-null summary
  3. Live `research.live.spec.ts` updated and green; subagent events asserted in real run

---

## Estimated wall-clock & subagent budget

- **Workers:** 6 (one per milestone, serial)
- **Validators:** ~12 (Scrutiny + User-Testing per milestone where UI is touched)
- **Retry budget:** ≤3 per milestone
- **Realistic worker count if retries hit:** 6–18
- **Wall-clock estimate:** ~7 days calendar (1 week, focused scope)

## Kill-switch / rollback criteria

Mission stops and surfaces to the user if any of these hit:

- M1 spike concludes NO-GO AND the custom fallback path also fails to produce a working hello-world agent within 1 retry
- Any single milestone fails 3 worker attempts in a row
- Wall-clock regresses > 1.5x M1 baseline on bulk-article queries (PRD rollback criterion)
- Subagents panel UX confuses the user (subjective; maintainer call)
- New integration test for subagent events flakes > 20% of the time

In any of these cases, save partial work, write the partial mission report, and hand back to the user with a short "stuck on X, options are Y/Z" note.

## Out-of-scope reminders (from PRD)

- GPU / multi-Ollama-instance support
- External LLM providers (OpenAI / Anthropic) — Ollama-only
- Per-question summary store (cache lives in `articles.summary`)
- Subagent retry policy (one attempt per dispatch)
- Per-skill failure policy (flat best-effort)
- `fetch_full_article` and `list_sources` skills (deferred)
- Streaming subagent token output to the frontend
- Background job queue / Celery

---

## Mission state log

State updates land here as milestones complete. The orchestrator appends after each milestone — this is the broadcast pattern, the single source of truth for the run.

### 2026-05-08 — Phase 1 complete
- Design context written: `docs/designs/per-article-subagents.md`
- PRD written: `docs/prds/per-article-subagents.md`
- Six issue files written:
  - `docs/issues/per-article-subagents-1-deepagents-spike.md`
  - `docs/issues/per-article-subagents-2-skills.md`
  - `docs/issues/per-article-subagents-3-subagent-pool.md`
  - `docs/issues/per-article-subagents-4-rewrite-agent.md`
  - `docs/issues/per-article-subagents-5-frontend-panel.md`
  - `docs/issues/per-article-subagents-6-ingestion-and-validation.md`
- Mission plan written: this file
- **Next step:** Phase 2 — surface plan to user and wait for explicit approval before spawning M1 worker.

### Phase 3 log (to be filled in during execution)
_Each milestone appends a one-paragraph entry: worker commit SHA, validator verdicts, retries, learnings. Empty until Phase 2 unlocks._

---

## How this mission was built

The mission follows the daisy-chain pattern from `~/.claude/skills/missions/SKILL.md`:

1. `grill-me` — produced the design context (3 rounds of questions, 12-of-12 user answers locked the architecture)
2. `write-prd` — produced the PRD with 6 milestones and explicit validation contracts
3. `write-issue` × 6 — produced one ticketable issue per milestone
4. `missions` — produced this plan and will execute Phase 3 serially with adversarial validators after Phase 2 approval

## Predecessor mission

This mission builds on the completed [Agentic Research Mode mission](./agentic-research-report.md) — Mission 1's `AgenticResearchService` is what M4 will rewrite end-to-end.
