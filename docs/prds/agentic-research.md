# PRD: Agentic Research Mode

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Status         | Draft                                                          |
| Author         | duc                                                            |
| Owner          | duc (eng + product, single-maintainer)                         |
| Stakeholders   | — (single-user portfolio piece)                                |
| Created        | 2026-05-08                                                     |
| Last updated   | 2026-05-08                                                     |
| Target ship    | 2026-05-17 (Sun, end of next week — ~10 days)                  |
| Design context | [docs/designs/agentic-research.md](../designs/agentic-research.md) |

## Summary

Replace the misnamed "Agentic Research Mode" tab with a real multi-step
LLM agent. The agent decomposes a user's research question into 3-5
sub-questions, runs internal semantic search per sub-question against
`news.db`, and streams a structured markdown report back via SSE — phase
chips above, token-by-token report below. Pinned to `gpt-oss:20b` for the
LLM calls; export-only persistence (no DB-backed report history); single
in-flight run per user. Direct cutover replaces the current single-
semantic-search call.

## Problem

The Research tab today is the most visibly fake feature in the app: it
labels itself "Agentic Research Mode" but runs a single semantic-search
query and renders an empty "Articles Analyzed: 0, Sources Used: 0"
report. Recruiters click it, see nothing, and rightly conclude the
"agentic" claim is decorative. For a backend / infra / platform-
engineering portfolio, that's a credibility hit.

A real multi-step agent — decomposing the question, running multiple
searches, synthesizing with citations, streaming progress — demonstrates
exactly the engineering chops the audience cares about: LLM
orchestration, SSE plumbing, structured output, error handling, citation
rigor.

## Goals & non-goals

### Goals
- Research tab consumes a real multi-step agent, not a single search
- Agent decomposes every question into 3-5 sub-questions before searching
- Output is a structured markdown report with executive summary, key
  findings, trends & themes, and a numbered sources section with inline
  `[N]` citations
- Wall-clock under 5 minutes per query on the maintainer's CPU
- Live UX shows a phase chip (`Decomposing → Searching → Synthesizing →
  Done`) AND the report streaming in token-by-token via SSE
- Sub-questions that find nothing don't fail the run — the report says
  "could not find data on X"
- Export-only — user can copy the markdown or download a `.md` file;
  no DB persistence
- Single in-flight run per user; submit button disabled while running
- New Playwright spec exercises the full SSE roundtrip plus the
  8-category UX rubric

### Non-goals
- External web search (DuckDuckGo, Brave, scraping)
- Persisting reports to a `research_reports` DB table
- Shareable public `/research/<slug>` URLs
- Tool-using agent (calling `/api/digest`, `/api/news/stats`,
  knowledge-graph endpoints, etc.)
- Iterative chat / follow-up refinement
- Quantitative table or chart output
- Configurable model per request — pinned to `gpt-oss:20b`
- Smart "trivial question" triage that skips decomposition
- Concurrent runs / job queue / background notification

## Users & use cases

### Primary user
The maintainer (single-user portfolio piece). Types a research question
when a topic is too broad for the news feed but too narrow for the
digest.

### Secondary user
Backend / infra / platform-engineering recruiters who:
1. Type a real question, watch the agent decompose + search + synthesize
2. Read the `frontend/e2e/research.spec.ts` and the
   `agentic_research_service.py` source to evaluate code quality

### Use cases
1. **Topic deep-dive.** Maintainer asks "what's the state of Anthropic's
   funding in the past month?" — agent decomposes into investor list,
   round size history, comparison to competitors. Streams a 4-section
   report citing TechCrunch + Ars Technica articles.
2. **Recruiter demo.** Recruiter clicks Research tab, types "AI chip
   announcements from this week", watches the phase chip cycle through
   all stages while the report streams in live. The Sources section has
   real article URLs that resolve when clicked.
3. **Empty-data graceful.** Maintainer asks something the corpus has no
   data on ("quantum-computing news from Q3 2026"). Agent returns
   structured report with "Could not find data on X" sections explicitly,
   not a 500 error or empty page.

## Requirements

### Functional
- New `AgenticResearchService` in
  `backend/src/services/agentic_research_service.py` with a single
  public async generator `run(question: str)` that yields events shaped
  `{type: "phase" | "token" | "done" | "error", data: ...}`
- Service flow:
  1. Emit `phase: "Decomposing"`
  2. Call Ollama (`gpt-oss:20b`) with strict JSON-output prompt
     producing `{"sub_questions": [str, str, str, ...]}` (3-5 items)
  3. Validate JSON; on parse failure, retry once with stricter prompt;
     if still bad, treat the original question as a single sub-question
  4. For each sub-question: emit `phase: "Searching (i/N)"`, run the
     existing semantic-search internal helper, capture top-K hits (K=5)
  5. Emit `phase: "Synthesizing"`
  6. Build final synthesis prompt with the user's question + all
     sub-question results + instruction to emit a structured markdown
     report with `[N]` citations matching a `## Sources Used` section
  7. Stream tokens from Ollama as `phase: "token"` events
  8. Emit `phase: "done"` with the final assembled report
- New route `POST /api/research` that accepts `{question: str}`, opens
  an SSE connection, and forwards the service generator's events
- SSE keepalive: emit `: keepalive\n\n` every 10s if no data flows, so
  the connection doesn't time out on a slow synthesize step
- Disconnect detection: backend cancels the in-flight Ollama generation
  if the SSE client closes
- Frontend `ResearchMode.tsx` rewritten:
  - Submit button disabled while a run is in flight
  - Phase chip above the report area, advancing through "Decomposing
    → Searching (i/N) → Synthesizing → Done"
  - Markdown rendered as it streams (re-render on each token, or buffer
    + render on whitespace boundaries — implementer's call)
  - "Copy markdown" and "Download .md" buttons in the report header
  - Inline `[N]` citations are anchor links scrolling to `#source-N`
- New Playwright spec `frontend/e2e/research.spec.ts` covering:
  - Submit a real question
  - Phase chip advances through all stages
  - Token streaming actually streams (>1 distinct DOM text length over time)
  - Final report has ≥1 inline `[N]` citation
  - Clicking a `[N]` link jumps to the matching `#source-N` element
  - 8-category UX rubric (no entities, real sources, no overflow on the
    streaming pane, console clean during stream)
- Single in-flight enforcement: backend rejects a second concurrent
  `POST /api/research` with HTTP 429; frontend's submit button is
  already disabled but the 429 is the safety net

### Non-functional
- **Performance**: median wall-clock under 5 minutes against
  `gpt-oss:20b` on the maintainer's CPU; first SSE phase event within
  3 seconds of submit
- **Reliability**: a single agent crash does not crash the FastAPI
  process; errors flow through SSE as a structured `error` event
- **Security**: no auth (consistent with the rest of the app); no
  outbound network calls beyond Ollama on `localhost:11434`
- **Compatibility**: existing `/api/search/semantic` endpoint stays
  alive as an internal tool / debugging surface; existing 16 contract
  tests + 25 Playwright tests must stay green
- **Code quality**: agent service has a docstring covering the loop +
  retry semantics; SSE event shape documented as a Pydantic model;
  every Ollama call is wrapped in a context manager that logs
  `start / end / duration / token-count`

## Success metrics

### Leading indicators (week 1 after deploy)
- 5 manual queries by the maintainer all complete in under 5 minutes
- Each produces a report with ≥3 sub-questions and ≥1 cited source
- Playwright `research.spec.ts` runs green 5 consecutive times

### Lagging indicators (30 days)
- Decomposer JSON validity rate > 80% on first attempt across logged runs
- Zero "agent crashed mid-stream" incidents
- Maintainer continues to use the Research tab at least once a week
  (proxy for: it's actually useful, not just demoware)

### Rollback criteria (any one triggers a revert to single-search)
- Decomposer returns invalid JSON > 50% of the time across a week
- Average wall-clock > 5 minutes on the maintainer's CPU across a week
- Playwright `research.spec.ts` goes red post-deploy
- User-Testing rubric flags content-integrity failures (hallucinated
  citations, fake article URLs, `[object Object]` in stream, etc.)

## Rollout plan

**Strategy: direct cutover.** Once the agent works end-to-end and tests
pass, the Research tab swaps from `/api/search/semantic` to
`/api/research`. The legacy endpoint stays alive as an internal tool but
the user-facing call is gone. No feature flag, no toggle UI.

1. **Days 1-3 (May 8-10)** — Milestones 1-2: Agent core service +
   SSE endpoint. All localhost.
2. **Days 4-5 (May 11-12)** — Milestone 3: Frontend SSE consumption
   + phase chip + streaming markdown.
3. **Day 6 (May 13)** — Milestone 4: Citations + cancel + error UX.
4. **Day 7 (May 14)** — Milestone 5: Playwright `research.spec.ts` +
   contract test for the SSE endpoint.
5. **Days 8-10 (May 15-17)** — Buffer for validator-spawned retries
   and any rubric failures the User-Testing Validator surfaces.

## Milestones & validation contracts

### Milestone 1 — Agent core service (decompose + search + synthesize) *(M, ~1.5 days)*

**Goal.** Backend service produces a complete report (string) for a
question, end-to-end, non-streaming first.

**Validation contract:**
- `AgenticResearchService.run(question)` is an async generator
- Calling `await service.run("test")` and consuming all events yields a
  sequence of `phase: "Decomposing"`, then 1+ `phase: "Searching"`,
  then `phase: "Synthesizing"`, then exactly one `phase: "done"`
- The decomposer's JSON output is parsed via a strict schema; invalid
  JSON triggers a single retry, then falls through to single-question
  mode
- Final assembled report is a non-empty string with at least one `[N]`
  citation marker and at least one entry in `## Sources Used`
- Service unit-tested in isolation with a mocked Ollama client
- 16 contract tests still pass

### Milestone 2 — SSE endpoint *(S, ~0.5 day)*

**Goal.** `POST /api/research` exposes the agent over SSE; events
stream live; disconnect cancels the agent.

**Validation contract:**
- `POST /api/research` with `{question: str}` opens an SSE connection
- Each yielded service event is forwarded as a discrete SSE `data:` line
  with the JSON-encoded event
- Server emits `: keepalive\n\n` every 10s if no real event is pending
- Closing the SSE client cancels the in-flight Ollama generation (no
  zombie processes; Ollama logs show the cancellation)
- Concurrent submit attempt returns HTTP 429
- New contract test `test_research_sse_smoke` in `run_e2e.py`: POST,
  read stream, assert at least one `phase` event arrives within 5s

### Milestone 3 — Frontend SSE consumption *(M, ~1 day)*

**Goal.** Research tab consumes the SSE endpoint and renders a phase
chip plus streaming markdown.

**Validation contract:**
- `ResearchMode.tsx` opens an SSE connection on submit (using
  `EventSource` or `fetch` + `ReadableStream`)
- Phase chip above the report shows `Decomposing → Searching (i/N) →
  Synthesizing → Done` matching the events received
- Submit button disabled while a run is in flight; re-enabled on
  `done` or `error`
- Markdown report streams in token-by-token (re-rendered on every
  event); typography matches the rubric (no overflow, no raw entities)
- Existing 25 Playwright tests stay green
- New behaviour: a placeholder Playwright assertion confirms the
  endpoint is being called (full Playwright spec lands in M5)

### Milestone 4 — Citations + cancel + error UX *(S, ~0.5 day)*

**Goal.** Inline citations work as anchor links; the user can cancel a
run; errors surface gracefully.

**Validation contract:**
- The synthesis prompt instructs the model to emit `[N]` citations
  matching numbered entries in `## Sources Used`
- Markdown post-processing replaces each `[N]` with an anchor
  `<a href="#source-N">[N]</a>` that scroll-jumps to the matching source
- "Copy markdown" and "Download .md" buttons render the report
- A "Cancel" button visible while running; clicking it closes the SSE
  connection (which the backend handles per M2)
- An `error` event from the SSE shows a clear "research interrupted —
  retry?" panel with a Retry button
- Hover state on inline citations: cursor pointer + underline

### Milestone 5 — Playwright + contract tests *(S, ~0.5 day)*

**Goal.** End-to-end test coverage matching the new behaviour.

**Validation contract:**
- New `frontend/e2e/research.spec.ts`:
  - Submit a real research question
  - Wait for phase chip to advance through all stages
  - Assert token streaming actually streams (DOM text length grows over
    time, not all-at-once)
  - Assert final report contains at least one `[N]` inline citation
  - Click an inline citation; assert the page scrolls to a matching
    `#source-N` element
  - Run the 8-category UX rubric on the rendered report
- New `test_research_sse_smoke` in `run_e2e.py` — a stdlib-only contract
  test that opens the SSE connection via urllib + manual stream parse,
  asserts at least one `phase` event arrives
- Suite runtime under 90 seconds total
- 16/16 contract + 26/26 Playwright (25 existing + 1 new) green

## Dependencies

- **Internal**: existing `/api/search/semantic` endpoint must continue
  to work (the agent uses it as an internal tool); existing
  `EmbeddingRepository` keyword-fallback path stays functional
- **External**: `gpt-oss:20b` already pulled (~13 GB); Ollama running
  on `localhost:11434`. No new external services.
- **Blockers / unblocks**: blocks nothing. Unblocks the "real demo"
  story for the Research tab, which is the most visibly fake tab today.

## Risks & mitigations

| Risk                                                        | Likelihood | Impact | Mitigation                                                                                                  |
|-------------------------------------------------------------|------------|--------|-------------------------------------------------------------------------------------------------------------|
| `gpt-oss:20b` produces invalid JSON for sub-questions       | High       | Med    | Strict parser + 1 retry with stricter prompt; fall through to single-question mode if still bad             |
| Synthesis hallucinates citations or article URLs            | Med        | High   | Filter the synthesis output to only cite sources actually returned by the search step; UX rubric test catches `[object Object]` / fake URLs |
| `gpt-oss:20b` OOMs the user's machine during synthesis      | Med        | High   | Catch the failure, return SSE `error` event with provider-fallback hint                                     |
| SSE keepalive too aggressive/lax                            | Low        | Low    | 10s keepalive interval; tune via env var if needed                                                          |
| Playwright SSE testing flaky                                | Med        | Med    | Use `EventSource` + race against a `Promise.race(timeout)`; cap test runtime at 60s                         |
| Wall-clock breaches 5-minute cap                            | Med        | High   | Server-side timer aborts the agent at 5min and emits the partial report                                     |
| Two concurrent submits slip past the disabled button        | Low        | Low    | Backend rejects with 429; frontend shows the error surface                                                  |
| Citations don't anchor (broken markdown links)              | Med        | Med    | Strict markdown post-processing; Playwright test asserts each `[N]` resolves to `#source-N` in the DOM      |
| 10-day timeline slips                                       | Med        | Low    | Milestones are independently shippable; non-goals already trimmed                                           |
| Direct cutover regresses for users who liked the old search | Low        | Low    | Single-user app; the legacy endpoint stays alive as a debug surface                                         |

## Open questions

- **Phase-chip wording and animation** — "Decomposing" vs "Planning" vs
  "Sketching" vs an icon. Bikeshed-able. *Owner: duc, decide during M3.*
- **Source snippet vs. title-only in the Sources section** — including
  a 200-char snippet per source is more useful but harder to render
  without tripping the rubric. *Owner: duc, decide during M4.*
- **Whether to expose model choice as a query param** even though we're
  pinned to `gpt-oss:20b`. *Owner: duc, decide during M2.*
- **Whether the decomposer prompt should include corpus metadata**
  (available sources, date range, top categories). *Owner: duc, decide
  during M1.*

## Out of scope (FAQ-style)

**Q: Will the agent search the live web?**
A: No. Internal corpus only. Web search is an explicit non-goal for v1.

**Q: Can I see my past research reports?**
A: No, not in v1. Reports are export-only — copy or download the
markdown. A `research_reports` DB table is on the parking lot for v2.

**Q: Why `gpt-oss:20b` instead of a smaller, faster model?**
A: Smaller models (1B-7B) consistently fail JSON-output assertions and
can't reliably decompose questions into clean sub-queries. The 20B model
is already pulled on this machine and the wall-clock budget covers it.

**Q: What if Ollama is down?**
A: The SSE endpoint returns an `error` event immediately; the frontend
shows a "research backend unavailable" surface. The rest of the app
(news feed, digest, knowledge graph) stays functional.

**Q: Is this going to use my paid OpenAI / Anthropic API key?**
A: No. Local Ollama only. Same constraint as the rest of the app.

## Appendix

- **Source design context**: [docs/designs/agentic-research.md](../designs/agentic-research.md)
- **Skill suite that orchestrates this build**:
  - [grill-me](../../.claude/skills/grill-me/SKILL.md) — design context
  - [write-prd](../../.claude/skills/write-prd/SKILL.md) — this doc
  - [write-issue](../../.claude/skills/write-issue/SKILL.md) — per-milestone tickets
  - [missions](../../.claude/skills/missions/SKILL.md) — orchestrated execution
  - [test-app-e2e](../../.claude/skills/test-app-e2e/SKILL.md) — validation
- **Existing E2E baseline**: 16 contract tests + 25 Playwright tests,
  all green at commit `26a55e0`
- **Conversation log**: see design context, sections "Round 1-3"
