# [Feature] Rewrite ResearchMode.tsx to consume the SSE agent stream

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, sse, ux                                                      |
| Linked PRD     | [docs/prds/agentic-research.md](../prds/agentic-research.md) — Milestone 3 |
| Linked design  | [docs/designs/agentic-research.md](../designs/agentic-research.md)     |

## Context
With M1 + M2 in place, the backend has a real agent + an SSE endpoint.
The Research tab still calls the old `/api/search/semantic` and renders a
stub. M3 is the user-facing direct cutover: rewrite `ResearchMode.tsx` to
open an SSE connection on submit, drive a phase chip from the streamed
events, and render the markdown report token-by-token as it arrives.

## Description
**Today:** `frontend/src/components/ResearchMode.tsx` calls
`/api/search/semantic` once on submit and renders a static `0 results /
0 sources used` stub.

**After this change:** On submit, `ResearchMode.tsx` opens an SSE
connection to `POST /api/research` with the question in the body, then:

- Disables the submit button while the run is in flight; re-enables on
  `done` or `error`
- Renders a phase chip above the report area showing one of:
  `Decomposing → Searching (i/N) → Synthesizing → Done`. The chip text
  comes directly from the `phase` field on incoming events
- Buffers `phase: "token"` events and re-renders the markdown report on
  every token (or every whitespace boundary — implementer's call, but
  the DOM text length must visibly grow during the stream, M5 asserts
  this)
- Renders the markdown via the existing markdown renderer used elsewhere
  in the app (look for the markdown component used in the Chat tab or
  elsewhere; do NOT introduce a new dependency)
- On `phase: "error"`, replaces the report area with a "research
  interrupted — retry?" panel; clicking Retry re-submits the same
  question
- On `phase: "done"`, finalises the rendered report and exposes "Copy
  markdown" + "Download .md" buttons (the buttons themselves land in M4
  — placeholder onClick is fine for M3)
- The submit input is cleared / kept based on existing UX convention;
  do not change that behaviour
- Uses `fetch` + `ReadableStream` (NOT `EventSource`) because POST-with-
  body SSE is not supported by `EventSource`. Parse the stream manually:
  split on `\n\n`, filter `:`-prefixed keepalive frames, JSON-parse the
  `data:` payload

`frontend/src/config/api.ts` gains a new endpoint
`research: "/api/research"` (already drafted in the PRD; confirm and add
if missing).

## Acceptance criteria
- [ ] `frontend/src/config/api.ts` exports `research: "/api/research"`
- [ ] `ResearchMode.tsx` no longer references `/api/search/semantic`
- [ ] On submit, the network panel shows a single `POST /api/research`
      request that stays open for the duration of the run
- [ ] The phase chip text changes at least 3 times during a real run
      (Decomposing → Searching → Synthesizing → Done)
- [ ] The rendered report's text length grows over time during the
      stream — captured by a Playwright placeholder assertion in this
      milestone, full Playwright spec lands in M5
- [ ] The submit button is disabled while a run is in flight and
      re-enabled when `phase: "done"` or `phase: "error"` arrives
- [ ] An `error` event renders a "research interrupted — retry?" panel
      with a Retry button that re-submits the same question
- [ ] All 25 existing Playwright tests still pass:
      `cd frontend && npx playwright test`
- [ ] No raw HTML entities (`/&#\d+;/`), no `[object Object]`,
      no `undefined`/`null` text appears in the rendered report
      (asserted by the rubric helpers in `frontend/e2e/_lib/rubric.ts`)
- [ ] No console errors during a successful run (asserted via
      `installConsoleErrorListener` from the rubric library)

## Implementation notes
Files likely involved:
- `frontend/src/components/ResearchMode.tsx` — full rewrite
- `frontend/src/config/api.ts` — add the endpoint
- `frontend/src/App.tsx` — pass the endpoint into ResearchMode if the
  component takes it as a prop (check current shape)
- Whichever markdown component is already used in `Chat.tsx` or
  similar — reuse, do NOT add a new lib
- `frontend/e2e/research.spec.ts` — placeholder assertion for this
  milestone; full spec lands in M5

Gotchas:
- `EventSource` cannot send POST bodies. Use `fetch` with
  `ReadableStream` and a manual line-buffered parser. See MDN's
  "Using server-sent events" + the manual-parse pattern
- Re-rendering on every token can flood React. Throttle the markdown
  re-render via `requestAnimationFrame` or batch on whitespace if you
  see jank — but make sure the streaming visibly progresses, M5 asserts
  growing DOM text length
- Cancellation: if the user navigates away mid-run, abort the fetch
  via `AbortController` so the backend's `is_disconnected` poll fires
- Citation anchor links are M4's job; for M3 just render the raw
  `[N]` text untouched

## Out of scope
- Citation `<a href="#source-N">` post-processing (M4)
- Cancel button (M4)
- Copy / Download .md handlers (M4 wires them up)
- The full Playwright spec for the streaming flow (M5)

## Verification
- Manual: type a real question, watch the phase chip cycle, watch the
  report stream in token-by-token
- Manual: open DevTools Network panel, confirm a single long-lived
  `POST /api/research` request
- Manual: open DevTools Console, run a query end-to-end, confirm zero
  `console.error` lines
- `cd frontend && npx playwright test` exits 0 (25/25 existing tests)

## Risks
- `fetch` + `ReadableStream` parsing is less battle-tested than
  `EventSource` — pin a single pattern early and reuse
- React re-render storm during streaming — throttle if needed
- Markdown renderer may eagerly parse incomplete tokens (e.g. an open
  `**` with no closing). Acceptable; the final `done` re-render will
  finalise the markup
