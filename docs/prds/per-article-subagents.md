# PRD: Per-article subagents + deepagents SDK

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Status         | Draft                                                                  |
| Author         | duc                                                                    |
| Owner          | duc (eng + product, single-maintainer)                                 |
| Created        | 2026-05-08                                                             |
| Last updated   | 2026-05-08                                                             |
| Target ship    | 2026-05-15 (~7 days)                                                   |
| Design context | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Summary

Replace the M1 `AgenticResearchService` with a deepagents-backed
implementation that **isolates per-article reasoning into subagent
contexts**. The orchestrator agent never sees raw article body text —
only IDs and per-article summaries returned by subagents. A
`max_concurrent = 4` semaphore-bounded pool runs subagent work in
parallel against Ollama. Four skills (`search_articles`,
`summarize_article` with cache reuse, `extract_entities`,
`query_knowledge_graph`) are exposed via deepagents tool registry.

Subagent telemetry events (start/done/error per subagent) are added to
the SSE stream. The frontend renders a "Subagents" panel showing
per-article progress in real time. Existing public SSE phase events
(`Decomposing → Searching → Synthesizing → Done`) are preserved so
M3+M4 work stays compatible.

## Problem

The current M1 service stuffs every retrieved article's content into a
single synthesis prompt. On bulk-article queries this either degrades
synthesis quality (long-context attention dilution) or risks OOMing
`gpt-oss:20b` on CPU. There's also no concurrency — subagent-style
per-article work happens serially inside one big prompt, capping
throughput.

This is the central architectural debt left from Mission 1. The
"agentic" claim becomes much sharper when you can *see* per-article
subagents firing in parallel against the corpus.

## Goals & non-goals

### Goals

- Replace M1 internals with deepagents-backed agent loop
- Per-article subagent contexts: each subagent's prompt contains ONLY
  that article + the user's question
- `max_concurrent = 4` bounded pool (configurable via env var)
- 4 skills implemented as deepagents tools, wrapping existing services
- Cache reuse for `summarize_article` (read from `news.db.summary` if
  fresh, else generate)
- Best-effort subagent failure semantics
- Subagent telemetry events in the SSE stream
- Frontend Subagents panel rendering per-article progress
- Ingestion summarization migrated to use the same `summarize_article`
  skill (one summarization implementation, two callers)
- Existing 17 contract + 29 Playwright tests stay green; 1 new
  integration test for subagent events; updated mocks in
  `research.spec.ts` to cover new event shape

### Non-goals

- GPU / multi-Ollama-instance concurrency
- External LLM providers (still Ollama-only)
- Per-question summary store (cache lives in `articles.summary` column)
- Subagent retry policy (one attempt; v2)
- Configurable per-skill failure policy (flat best-effort)
- `fetch_full_article` and `list_sources` skills (deferred)
- Streaming subagent token output to the frontend
- Frontend redesign of the report area
- Background job queue / Celery

## Users & use cases

### Primary user
The maintainer. Submits research questions and watches the agent work.

### Secondary user
Backend / infra / platform engineering recruiters who:
1. Click into the Research tab and watch real subagents fire in
   parallel via the new Subagents panel
2. Read `agentic_research_service.py` and `services/agent_skills/` to
   evaluate the deepagents integration

### Use cases

1. **Bulk-article query** — "What are the major themes in AI safety
   coverage from this past month?" Returns 8 articles. Agent dispatches
   8 `summarize_article` subagents (4 in flight at a time), aggregates
   their summaries, synthesizes the report. Wall-clock cuts roughly in
   half vs M1's serial approach.
2. **Cache-warm query** — Maintainer runs the same query twice. Second
   run hits the summary cache for every article, completes 70%+ faster.
3. **Failed-subagent demo** — Test injects an Ollama timeout into one
   subagent. Run continues; report explicitly notes "Could not analyze
   article #X" and the Subagents panel shows that one row in error
   state.

## Requirements

### Functional

- Install deepagents (or langchain-deepagents) and pin the version
- New `services/agent_skills/` package with one file per skill:
  - `search_articles.py` — wraps `SearchService.search`
  - `summarize_article.py` — wraps `SummarizationService` + reads
    `articles.summary` cache; cache hit returns immediately, miss
    generates and writes back
  - `extract_entities.py` — wraps `EntityExtractionService.process_article`
  - `query_knowledge_graph.py` — walks the entity/co-mention graph
- Each skill is a deepagents `Tool`/`Skill` with proper schema
- New `services/subagent_pool.py` exposing `SubagentPool` with
  `asyncio.Semaphore(MAX_CONCURRENT_SUBAGENTS)` and a `dispatch(skill,
  args, on_event)` API
- Rewritten `services/agentic_research_service.py`:
  - Uses deepagents `Agent` with the 4 skills registered
  - Async generator `run(question)` yields events compatible with M1
    plus new `subagent` events
  - Orchestrator's prompt receives ONLY article IDs + summaries
    (verified via context-engineering hooks)
- Extended `models/article.py` `AgentEvent` to allow `type =
  "subagent"` with extra fields `skill`, `article_id`, `duration_ms`,
  `message`
- `core/config.py` adds `max_concurrent_subagents: int = 4`
- Frontend `ResearchMode.tsx` parses `subagent` events and renders a
  collapsible "Subagents" panel with rows
- `summarize_article` skill is reused by `summarization_orchestrator.py`
  at ingest time
- Cache-reuse heuristic: hit if `articles.summary != null` AND
  (`focus_question is None` OR `hash(focus_question[:100]) ==
  hash(cached_focus_question[:100])` — implemented as a small JSON
  blob `articles.summary_meta` if needed, else just unconditional
  reuse on null `focus_question`)

### Non-functional

- **Performance**: median wall-clock ≤ M1's median (concurrency offsets
  per-article overhead). Cache-warm queries ≥ 50% faster.
- **Reliability**: a subagent crash never crashes the FastAPI process.
  Errors flow through SSE as `subagent: error` events
- **Security**: no auth, no outbound calls beyond Ollama on
  `localhost:11434`
- **Compatibility**: existing 17 contract + 29 Playwright tests stay
  green. New test count: +1 integration test for subagent SSE events,
  +1 Playwright test for the Subagents panel
- **Code quality**: each skill has a docstring covering input/output
  schema and side effects. Each Ollama call inside subagents is wrapped
  in the existing `_ollama_call` logger
- **Observability**: every subagent dispatch emits structured logs
  with `skill_name`, `article_id`, `duration_ms`, `cache_hit`,
  `status`. The Subagents panel surfaces this to the user

## Success metrics

### Leading indicators (week 1 after deploy)

- 5 manual queries by the maintainer all complete in under 5 minutes
- Each produces a report with ≥3 sub-questions and ≥1 cited source
- Cache-warm queries are demonstrably faster than cold ones
- Subagents panel shows ≤4 concurrent rows (max_concurrent honored)

### Lagging indicators (30 days)

- Zero "subagent leak" incidents (orchestrator prompt size bounded)
- Cache-hit rate > 50% for repeated queries
- Maintainer continues to use the Research tab at least once a week

### Rollback criteria (any one triggers a revert to M1)

- deepagents SDK proves incompatible with our async-generator pattern
  AND custom fallback also fails
- Wall-clock regression > 1.5x M1 baseline on bulk queries
- Subagents panel UX confuses the user (subjective; maintainer call)
- New integration test for subagent events flakes > 20% of the time

## Rollout plan

**Strategy: direct cutover.** Same as Mission 1 — flip
`AgenticResearchService` to the new implementation; legacy code path
removed.

1. **Days 1-2 (May 9-10)** — Milestone 1: deepagents spike. Decide
   adopt-or-fallback at end of M1.
2. **Days 2-3 (May 10-11)** — Milestone 2: 4 skills.
3. **Days 3-4 (May 11-12)** — Milestone 3: SubagentPool +
   per-article context isolation.
4. **Day 5 (May 13)** — Milestone 4: replace M1 internals; preserve
   public SSE shape; emit subagent events.
5. **Day 6 (May 14)** — Milestone 5: frontend Subagents panel.
6. **Day 7 (May 15)** — Milestone 6: tests + cache-reuse cutover for
   ingestion + final validation pass.

## Milestones & validation contracts

### Milestone 1 — deepagents spike + adopt/fallback decision *(M, ~1.5 days)*

**Goal.** Install deepagents, build a "hello world" agent with one
skill (`search_articles`), verify it talks to Ollama, decide whether to
adopt or fall back to a custom asyncio-based pool.

**Validation contract:**
- `pip install deepagents` (or langchain-deepagents) succeeds; version
  pinned in `backend/requirements.txt`
- A scratch script `backend/scripts/spike_deepagents.py` instantiates a
  deepagents `Agent` with one skill (`search_articles`), runs it
  against a hardcoded query, prints the agent's tool calls + final
  output
- A doc note `docs/notes/deepagents-api-surface.md` captures the
  package's main API + an explicit go/no-go decision with reasoning
- If GO: M2 proceeds with deepagents. If NO-GO: M2 builds a custom
  `SubagentPool` + dataclass-based skill registry instead. The PRD's
  remaining milestones are language-agnostic about which path was
  taken.

### Milestone 2 — 4 skills implementation *(M, ~1 day)*

**Goal.** Implement the 4 skills as deepagents tools (or fallback
custom skills), each wrapping an existing service.

**Validation contract:**
- `services/agent_skills/{search_articles,summarize_article,extract_entities,query_knowledge_graph}.py`
  each exist with a clear input schema and pure async functions
- `summarize_article` honors cache reuse: returns
  `{"summary": ..., "cache_hit": True}` when `articles.summary` exists
  and `focus_question` is None; otherwise generates via
  `SummarizationService` and writes back
- New unit tests in `backend/tests/unit/test_agent_skills.py` cover
  each skill happy-path + a cache-hit + cache-miss case for
  `summarize_article`
- All 17 existing contract tests still pass

### Milestone 3 — SubagentPool + per-article context isolation *(M, ~1.5 days)*

**Goal.** Build the bounded subagent pool. Each subagent runs in an
isolated context that contains ONLY the article + the user's question.

**Validation contract:**
- `services/subagent_pool.py` exposes `SubagentPool` with:
  - `__init__(self, max_concurrent: int = 4)`
  - `async def dispatch(self, skill_fn, args, on_event)` that emits
    `subagent: start|done|error` events
- At most `max_concurrent` skill_fn calls are in flight simultaneously
  (verified via test that submits 10 dispatches with 100ms sleeps and
  asserts max-in-flight via a counter)
- The subagent's input prompt size stays roughly constant regardless
  of how many sibling subagents are running (verified by per-call
  prompt-size logging)
- Best-effort failure: a `skill_fn` raising an exception emits a
  `subagent: error` event but does NOT propagate to the caller

### Milestone 4 — Rewrite AgenticResearchService *(L, ~1 day)*

**Goal.** Replace M1's `AgenticResearchService` with the
deepagents-backed agent loop. Same outer SSE phases. New subagent
events.

**Validation contract:**
- `services/agentic_research_service.py` rewritten end-to-end
- Existing 16 unit tests in `test_agentic_research_service.py`
  rewritten for the new implementation; all pass
- Existing 6 integration tests in `test_research_sse.py` pass with
  zero changes (M1's SSE shape preserved as backward-compat)
- New integration test asserts ≥1 `subagent: start` and matching
  `subagent: done` events arrive for a typical query
- The orchestrator's prompt to the LLM contains article IDs + summaries
  but NOT raw article body text (asserted via prompt-inspection
  fixture)
- 17 contract tests still green

### Milestone 5 — Frontend Subagents panel *(M, ~1 day)*

**Goal.** Render subagent telemetry in the UI.

**Validation contract:**
- `ResearchMode.tsx` parses `subagent` events and updates a state
  array of subagent rows
- A new collapsible "Subagents" panel appears below the phase chip,
  showing one row per article with: skill name, status badge
  (running/done/error), duration (when done)
- Panel auto-expands on first `subagent: start`; defaults to expanded
  during a run
- 8-category UX rubric still passes on the rendered Research surface
- Existing 5-test `research.spec.ts` mocks updated to include subagent
  events; all 5 still green
- 1 new test in `research.spec.ts` asserts: "Subagents panel renders
  ≥1 row when subagent events arrive"

### Milestone 6 — Ingestion migration + tests + final validation *(M, ~1 day)*

**Goal.** Migrate ingestion summarization to use the
`summarize_article` skill. Update all tests. Run full E2E.

**Validation contract:**
- `services/summarization_orchestrator.py` calls
  `agent_skills.summarize_article` instead of directly calling
  `SummarizationService`
- A backfill smoke test confirms newly-ingested articles still get
  summarized correctly
- Live `research.live.spec.ts` updated to assert subagent events
  arrive during a real Ollama-backed run
- All test counts: 17 contract + 6 integration + 5 (was 5) + 2 (live)
  + new subagent-panel + new SSE-subagent = at least 31 tests passing
- Run the live integration test once end-to-end as final smoke

## Dependencies

- **External**: `deepagents` package (or langchain-deepagents). Pinned
  in M1
- **Internal**: M1's existing services (`SearchService`,
  `SummarizationService`, `EntityExtractionService`,
  `EmbeddingService`, `ArticleRepository`) — all reused, none rewritten
- **Blockers / unblocks**: Blocks nothing. Unblocks "real subagent
  story" for the portfolio — the architecture becomes visibly
  multi-agent rather than internally faking it

## Risks & mitigations

| Risk                                                            | Likelihood | Impact | Mitigation                                                                                            |
|-----------------------------------------------------------------|------------|--------|-------------------------------------------------------------------------------------------------------|
| deepagents SDK doesn't fit our async-generator pattern          | Med        | High   | M1 spike has explicit go/no-go gate. Fallback is custom asyncio.Semaphore + dataclass skills          |
| `gpt-oss:20b` doesn't reliably do tool-use under deepagents     | Med        | High   | Test in M1 spike; fallback is hand-rolled JSON-output prompts (matches M1's existing pattern)         |
| max_concurrent=4 thrashes Ollama on CPU                         | Med        | Med    | Configurable env var; default 4, tunable down to 1                                                    |
| Cache-reuse returns stale or off-topic summary                  | Med        | Med    | Hash heuristic on focus_question prefix; null focus_question always reuses                            |
| Subagent failures cascade and break the run                     | Low        | High   | Best-effort with explicit gaps; one M3 unit test forces a subagent crash and asserts the run completes |
| Frontend Subagents panel breaks layout on mobile                | Low        | Low    | Responsive design; collapsible by default                                                             |
| Ingestion migration breaks the existing summarization pipeline  | Med        | High   | Ship behind a feature flag for one run; cut over once the smoke test confirms parity                  |
| Wall-clock regresses vs M1 baseline                             | Low        | Med    | Concurrency should help, not hurt. Rollback criterion if > 1.5x M1                                    |
| 1-week timeline slips                                           | Med        | Low    | Milestones are independently shippable; M5 (frontend) is non-blocking for backend correctness         |

## Open questions

- **deepagents version pin** — decided in M1. *Owner: duc, decide M1.*
- **Subagents panel default state** — auto-expand on first event vs.
  always-collapsed. *Owner: duc, decide during M5.*
- **summarize_article prompt template** — does
  `focus_question`-aware regeneration use the same template as
  ingestion? *Owner: duc, decide during M2.*
- **Ingestion feature flag rollout** — flag name + cleanup plan.
  *Owner: duc, decide during M6.*

## Out of scope (FAQ-style)

**Q: Will deepagents let us swap to OpenAI/Anthropic later?**
A: Yes — that's part of the appeal. But this mission stays Ollama-only.

**Q: What if deepagents is overkill for this?**
A: M1 has an explicit go/no-go gate. If the spike says no, we fall
back to a custom SubagentPool + dataclass skill registry. The
remaining milestones (M2-M6) are mostly the same either way.

**Q: Why max_concurrent=4 specifically?**
A: gpt-oss:20b on a single Ollama instance serializes internally; >4
mostly thrashes. 4 leaves headroom for the orchestrator's own LLM
calls overlapping with subagent calls.

**Q: Does this change the public API?**
A: The endpoint is unchanged. The SSE event shape is *additive* — new
`type: "subagent"` events appear, but all M1-era event types (phase,
token, done, error) still flow with identical fields. Old SSE
consumers (which we don't have any of) would just ignore unknown
event types.

## Appendix

- **Source design context**: [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md)
- **Mission 1 baseline**: [docs/missions/agentic-research-report.md](../missions/agentic-research-report.md)
- **Skill suite that orchestrates this build**:
  - grill-me — design context (this round of grill is logged in the design doc)
  - write-prd — this doc
  - write-issue — per-milestone tickets
  - missions — orchestrated execution
- **Existing E2E baseline**: 17 contract + 29 Playwright tests, all
  green at commit `947f9fd`
