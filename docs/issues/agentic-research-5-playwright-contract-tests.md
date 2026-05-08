# [Test] Playwright research.spec.ts + SSE contract test for /api/research

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Test                                                                   |
| Priority       | P1                                                                     |
| Estimate       | S                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | tests, playwright, e2e, sse                                            |
| Linked PRD     | [docs/prds/agentic-research.md](../prds/agentic-research.md) — Milestone 5 |
| Linked design  | [docs/designs/agentic-research.md](../designs/agentic-research.md)     |

## Context
M1-M4 ship the agent, SSE endpoint, frontend streaming, and citation/
cancel/error UX. M5 closes the loop with end-to-end test coverage: a new
Playwright spec exercises the full SSE roundtrip in the real UI, asserts
the 8-category UX rubric, and a stdlib-only contract test in `run_e2e.py`
provides a quick smoke for the SSE endpoint that doesn't require a
browser.

## Description
**Today (after M4):** The Research tab works end-to-end manually but has
no automated test asserting the streaming behaviour, citation anchoring,
cancel flow, or error path. The contract suite has 16 tests; the
Playwright suite has 25 tests; neither covers `/api/research`.

**After this change:**

1. **New `frontend/e2e/research.spec.ts`** with these tests:
   - **Submit + streaming flow** — type a real question, click Submit,
     wait for the phase chip to advance through `Decomposing →
     Searching → Synthesizing → Done`. Assert the rendered report's DOM
     text length grows over time (sample at 3 timepoints; the values
     must be strictly increasing to prove streaming is happening, not
     all-at-once)
   - **Citation anchoring** — after `done`, locate at least one `[N]`
     anchor in the report; click it; assert the page scrolls and the
     matching `#source-N` element is in the viewport
   - **Cancel flow** — submit a question; while a run is in flight,
     click Cancel; assert the phase chip resets, the submit button
     re-enables, and no `console.error` was logged
   - **Error UX** — submit a question against a back-end stubbed to
     emit `phase: "error"` immediately (use Playwright's
     `page.route(...)` to mock `POST /api/research`); assert the
     "Research interrupted" panel appears with a working Retry button
   - **Rubric pass** — run the 8 rubric helpers from
     `frontend/e2e/_lib/rubric.ts`: no HTML entities, no mojibake, no
     `undefined / null / [object Object]`, no horizontal overflow on
     the streaming pane, images render (if any), no duplicate sibling
     blocks, no `seed-*` / `mock-*` patterns, console-clean during the
     stream

2. **New stdlib contract test `test_research_sse_smoke`** in
   `.claude/skills/test-app-e2e/scripts/run_e2e.py`:
   - Opens `POST /api/research` via `urllib.request` with a JSON body
   - Reads the response stream manually (no SSE library)
   - Asserts at least one `data: ` line containing a `phase` field
     arrives within 5s
   - Closes the connection cleanly; asserts no exception

3. **Suite runtime budget**: the full Playwright suite (25 existing + 1
   new) must complete under 90 seconds on the maintainer's machine.
   Use a pre-warmed app + a short question to keep the SSE test snappy

## Acceptance criteria
- [ ] `frontend/e2e/research.spec.ts` exists and contains all 5 tests
      listed above
- [ ] `cd frontend && npx playwright test` exits 0 with 26/26 tests
      green (25 existing + 1 new spec file)
- [ ] The streaming-flow test asserts strictly-increasing DOM text
      length at 3 timepoints during the stream
- [ ] The citation-anchor test clicks a real `[N]` and asserts the
      target `#source-N` is in the viewport
- [ ] The cancel-flow test asserts no `console.error` logged
- [ ] The error-UX test uses `page.route` to mock the SSE endpoint;
      no real Ollama call required for that test
- [ ] All 5 tests run the rubric helpers from `_lib/rubric.ts` at the
      end and pass each one
- [ ] `test_research_sse_smoke` is added to `run_e2e.py`'s test
      registry; `python .claude/skills/test-app-e2e/scripts/run_e2e.py
      --skip-frontend` exits 0 with 17/17 contract tests
- [ ] Full suite wall-clock under 90 seconds:
      `cd frontend && time npx playwright test`
- [ ] A short README block in `frontend/e2e/research.spec.ts`'s file
      header documents how to re-run only this spec:
      `npx playwright test research.spec.ts`

## Implementation notes
Files likely involved:
- `frontend/e2e/research.spec.ts` — NEW
- `frontend/e2e/_lib/rubric.ts` — already exists; extend if a
  research-specific helper is needed (e.g.
  `assertCitationAnchorsResolve(page)`)
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — add
  `test_research_sse_smoke` and register it
- `frontend/playwright.config.ts` — confirm video recording is enabled
  for this spec (`video: 'retain-on-failure'`)

Gotchas:
- Strictly-increasing DOM text length is fragile if the markdown
  renderer is too aggressive about throttling. Sample at intervals
  long enough (e.g. 1s, 3s, 5s) to allow real progress; do NOT compare
  consecutive frames
- The error-UX mock must return a real `text/event-stream` content type
  with a properly-framed `data: {...}\n\n` body, otherwise the
  frontend's stream parser (M3) won't recognise it
- The cancel test depends on the AbortController plumbing landing in
  M3+M4. If it's not in place, the test will hang — fail fast with a
  10s timeout
- `urllib.request` does NOT decode chunked encoding by default; read
  raw bytes and split on `\n\n` manually
- Playwright's `page.route` only intercepts requests from the page
  itself, not from a fetch initiated outside the page context — this
  works because `ResearchMode.tsx`'s fetch IS page-context

## Out of scope
- Backend changes (those are M1+M2)
- Frontend behaviour changes (those are M3+M4) — this milestone is
  testing only
- Visual regression / screenshot tests
- Load testing or concurrent-run testing beyond M2's 429 contract

## Verification
- `cd frontend && npx playwright test` — 26/26 green, under 90s
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`
  — 17/17 green
- `cd frontend && npx playwright test research.spec.ts --reporter=list`
  — only the new spec runs, 5/5 green
- Open the recorded video for the streaming-flow test (in
  `frontend/test-results/`) and visually confirm the phase chip cycles
  and the report streams

## Risks
- SSE-via-Playwright flakiness — mitigated by increasing the
  timepoint gap and using `page.waitForFunction` rather than fixed
  delays where possible
- The 90s budget could slip if `gpt-oss:20b` is slow on the test
  machine. If breached, the streaming-flow test can use a shorter
  question or a slightly stubbed agent that runs faster while still
  exercising the SSE plumbing
- The error-UX test must not interfere with subsequent tests'
  network state — clear `page.route` handlers in `afterEach`
