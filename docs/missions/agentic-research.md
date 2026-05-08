# Mission: Agentic Research Mode

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Status         | **Phase 1 complete — awaiting Phase 2 approval**               |
| Owner          | duc (orchestrator)                                             |
| Created        | 2026-05-08                                                     |
| Target ship    | 2026-05-17 (Sun, ~10 days)                                     |
| Design context | [docs/designs/agentic-research.md](../designs/agentic-research.md) |
| PRD            | [docs/prds/agentic-research.md](../prds/agentic-research.md)   |
| Skill          | [~/.claude/skills/missions](../../.claude/skills/missions/SKILL.md) |

This mission replaces the misnamed "Agentic Research Mode" tab — currently
a single semantic-search call labelled as agentic — with a real multi-step
LLM agent that decomposes, searches, synthesizes, and streams results via
SSE. It is broken into 5 milestones, each with its own ticketable issue
and validation contract.

The orchestrator (this Claude session) will spawn one worker subagent per
milestone serially, then run scrutiny + user-testing validators in
parallel after each worker hands off, retrying up to 3 times per milestone
before surfacing to the user.

---

## Milestones (in order)

### M1 — Agent core service *(M, ~1.5 days)*
- **Issue:** [docs/issues/agentic-research-1-agent-core-service.md](../issues/agentic-research-1-agent-core-service.md)
- **Goal:** Build `AgenticResearchService.run(question)` async generator
  that decomposes → searches → synthesizes a structured markdown report
  with `[N]` citations. Non-streaming first.
- **Validation contract (top 3):**
  1. `await`-consuming `run("...")` yields the event sequence
     `Decomposing → Searching (i/N)+ → Synthesizing → done`
  2. Decomposer JSON parse-failure path retries once then falls through
     to single-question mode, run still completes
  3. Final report contains ≥1 `[N]` citation AND ≥1 entry in
     `## Sources Used`; 16 contract tests stay green; new unit tests
     cover happy path + invalid-JSON-retry + invalid-JSON-fallthrough +
     zero-hit sub-question

### M2 — SSE endpoint *(S, ~0.5 day)*
- **Issue:** [docs/issues/agentic-research-2-sse-endpoint.md](../issues/agentic-research-2-sse-endpoint.md)
- **Goal:** `POST /api/research` exposes the agent over SSE; events
  stream live; disconnect cancels the agent; second concurrent submit
  returns 429.
- **Validation contract (top 3):**
  1. `POST /api/research` returns `text/event-stream` with discrete
     `data: <json>\n\n` frames; first frame within 5s
  2. Closing the SSE client cancels the in-flight Ollama generation
     (verified by stub generator + test of `finally` handler)
  3. New `test_research_sse_smoke` in `run_e2e.py` opens the stream,
     parses lines, asserts a `phase` event arrives within 5s; 17/17
     contract tests green

### M3 — Frontend SSE consumption *(M, ~1 day)*
- **Issue:** [docs/issues/agentic-research-3-frontend-sse-consumption.md](../issues/agentic-research-3-frontend-sse-consumption.md)
- **Goal:** Rewrite `ResearchMode.tsx` to consume the SSE endpoint,
  drive a phase chip, and stream the markdown report. Direct cutover
  off `/api/search/semantic`.
- **Validation contract (top 3):**
  1. On submit, network panel shows a single long-lived
     `POST /api/research` request; phase chip text changes ≥3 times
     during a real run
  2. Rendered report's DOM text length grows over time during the
     stream (placeholder Playwright assertion lives here; full spec
     in M5)
  3. 25/25 existing Playwright tests stay green; rubric helpers
     (no entities, no `[object Object]`, no console.error) all pass
     during a run

### M4 — Citations + cancel + error UX *(S, ~0.5 day)*
- **Issue:** [docs/issues/agentic-research-4-citations-cancel-error-ux.md](../issues/agentic-research-4-citations-cancel-error-ux.md)
- **Goal:** Inline `[N]` citations become anchor links to
  `#source-N`; Cancel button aborts the SSE fetch; error events surface
  a "Research interrupted — retry?" panel; Copy / Download .md buttons
  get real handlers.
- **Validation contract (top 3):**
  1. After `done`, every `[N]` is wrapped in
     `<a href="#source-N" class="citation">`; clicking smooth-scrolls
     to the matching source anchor
  2. Cancel button visible only while running; clicking aborts the
     fetch and resets the UI; submit button re-enables
  3. On `phase: "error"`, "Research interrupted" panel appears with a
     working Retry button that re-submits the same question;
     25/25 existing Playwright tests still green

### M5 — Playwright `research.spec.ts` + SSE contract test *(S, ~0.5 day)*
- **Issue:** [docs/issues/agentic-research-5-playwright-contract-tests.md](../issues/agentic-research-5-playwright-contract-tests.md)
- **Goal:** New end-to-end spec exercising streaming + citations +
  cancel + error UX + 8-category UX rubric, plus a stdlib SSE smoke
  test in `run_e2e.py`.
- **Validation contract (top 3):**
  1. `frontend/e2e/research.spec.ts` contains 5 tests (streaming,
     citations, cancel, error, rubric) and all pass; full suite
     26/26 green under 90s
  2. Streaming test asserts strictly-increasing DOM text length at
     3 timepoints; citation test clicks `[N]` and asserts `#source-N`
     in viewport
  3. New `test_research_sse_smoke` in `run_e2e.py` is registered;
     17/17 contract tests green

---

## Estimated wall-clock & subagent budget

- **Workers:** 5 (one per milestone, serial)
- **Validators:** ~10 (Scrutiny + User-Testing per milestone, parallel)
- **Retry budget:** ≤3 per milestone (cap before surfacing)
- **Realistic worker count if retries hit:** 5–14
- **Wall-clock estimate:** 4–10 hours of orchestrator-side time over
  the 10-day calendar window. Slack absorbed by M5's buffer days
  (May 15–17) per the PRD.

## Kill-switch / rollback criteria

Mission stops and surfaces to the user if any of these hit:

- Any single milestone fails 3 worker attempts in a row
- Decomposer JSON validity rate measures < 50% across M1's unit tests
- M2 SSE endpoint can't keep a connection alive for 60s (proxy /
  buffering issue)
- `gpt-oss:20b` consistently OOMs the user's machine during synthesis
- Final Playwright suite breaches the 90-second runtime budget by
  more than 50% (i.e. > 135s)

In any of these cases, save partial work, write the partial mission
report, and hand back to the user with a short "stuck on X, options
are Y/Z" note.

## Out-of-scope reminders (from PRD)

- External web search (DuckDuckGo, Brave, scraping)
- Persisting reports to a `research_reports` DB table
- Tool-using agent (calling other API routes from the agent loop)
- Iterative chat / follow-up refinement
- Configurable model per request — pinned to `gpt-oss:20b`

---

## Mission state log

State updates land here as milestones complete. The orchestrator
appends after each milestone — this is the broadcast pattern, the
single source of truth for the run.

### 2026-05-08 — Phase 1 complete
- Design context written: `docs/designs/agentic-research.md` (216 lines)
- PRD written: `docs/prds/agentic-research.md` (360 lines)
- Five issue files written:
  - `docs/issues/agentic-research-1-agent-core-service.md`
  - `docs/issues/agentic-research-2-sse-endpoint.md`
  - `docs/issues/agentic-research-3-frontend-sse-consumption.md`
  - `docs/issues/agentic-research-4-citations-cancel-error-ux.md`
  - `docs/issues/agentic-research-5-playwright-contract-tests.md`
- Mission plan written: this file
- **Next step:** Phase 2 — surface plan to user and wait for explicit
  approval before spawning M1 worker.

### Phase 3 log (to be filled in during execution)
_Each milestone appends a one-paragraph entry: worker commit SHA,
validator verdicts, retries, learnings. Empty until Phase 2 unlocks._

---

## How this mission was built

The mission follows the daisy-chain pattern from
`~/.claude/skills/missions/SKILL.md`:

1. `grill-me` — produced the design context (3 rounds of questions,
   12-of-12 user answers landed on the recommended path)
2. `write-prd` — produced the PRD with 5 milestones and explicit
   validation contracts
3. `write-issue` × 5 — produced one ticketable issue per milestone
4. `missions` — produced this plan and will execute Phase 3
   serially with adversarial validators after Phase 2 approval
