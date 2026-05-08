# [Feature] Wire inline citations, cancel button, and error UX in Research tab

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | S                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, ux, citations                                                |
| Linked PRD     | [docs/prds/agentic-research.md](../prds/agentic-research.md) — Milestone 4 |
| Linked design  | [docs/designs/agentic-research.md](../designs/agentic-research.md)     |

## Context
M1-M3 land the agent, the SSE endpoint, and the streaming UI. M4 closes
the UX gap: inline `[N]` citations become clickable anchor links,
the user can cancel a run mid-flight, and error events surface as a
clear retry-able panel. Copy / Download .md buttons get real handlers.
This is the polish milestone before the final test pass in M5.

## Description
**Today (after M3):** Report streams in, inline `[N]` citations render
as plain text, no cancel button, error events show a placeholder, copy
and download handlers are stubs.

**After this change:**

1. **Citations as anchor links.** Once the report is finalised on
   `phase: "done"`, post-process the markdown so each inline `[N]`
   becomes `<a href="#source-N" class="citation">[N]</a>`. The
   numbered entries in `## Sources Used` get matching `id="source-N"`
   anchors. Hover state: `cursor: pointer; text-decoration: underline`.
   Clicking jumps the report container to the source — `scrollIntoView({
   behavior: "smooth", block: "start" })`
2. **Cancel button.** While a run is in flight, render a Cancel button
   next to the phase chip. Clicking it calls `AbortController.abort()`
   on the fetch (added in M3); the SSE connection closes and the
   backend's `is_disconnected` handler cancels the Ollama generation
   (M2 already covers this server-side)
3. **Error event panel.** When `phase: "error"` arrives, replace the
   report area with a panel: heading "Research interrupted",
   one-sentence message from the event's `data.message` field, and a
   Retry button that re-submits the same question. Distinguish from
   "still streaming" — the panel must NOT appear for partial-but-OK
   reports
4. **Copy markdown / Download .md.** Wire the buttons added as
   placeholders in M3:
   - Copy: `navigator.clipboard.writeText(report)` + a brief
     "Copied!" toast (use the existing toast component if present;
     otherwise a 2s `setTimeout` text swap is fine)
   - Download: build a Blob from the report markdown, trigger an
     `<a download="research-<timestamp>.md">` click

## Acceptance criteria
- [ ] After a successful run, every inline `[N]` in the rendered report
      is wrapped in `<a href="#source-N" class="citation">` with cursor
      pointer + underline on hover
- [ ] Clicking an inline `[N]` link smooth-scrolls to the matching
      `#source-N` anchor in the `## Sources Used` section
- [ ] A Cancel button is visible while a run is in flight and hidden
      when idle / done / errored. Clicking it aborts the fetch; the
      submit button re-enables; phase chip resets to idle
- [ ] On `phase: "error"`, the report area is replaced by a panel with
      heading "Research interrupted" and a Retry button. Clicking
      Retry re-submits the same question and the run starts again
- [ ] "Copy markdown" copies the full report to clipboard and shows a
      transient "Copied!" indicator
- [ ] "Download .md" downloads a file named
      `research-<ISO timestamp>.md` containing the report
- [ ] All 25 existing Playwright tests still pass:
      `cd frontend && npx playwright test`
- [ ] No console errors triggered by the citation post-processing,
      cancel flow, or download flow (rubric assertion)
- [ ] No horizontal overflow on the citation panel (rubric assertion)

## Implementation notes
Files likely involved:
- `frontend/src/components/ResearchMode.tsx` — citation post-processing,
  cancel handler, error panel, copy/download wiring
- Wherever the markdown renderer lives — confirm it lets you post-
  process the rendered HTML, or handle the `[N]` swap at the markdown
  source level before render
- Existing toast component (search for `useToast` or `Toast` in
  `frontend/src/components/`) — reuse for the "Copied!" indicator

Gotchas:
- Post-processing must run AFTER the final `done` event; doing it on
  every token would create flicker as `[N]` markers appear
- The `## Sources Used` section needs deterministic anchors. Build the
  ID list from the source ordering, not the model's output, so the
  anchor list is well-formed even if the model's section is malformed
- `AbortController` from M3: keep one instance per submit; reset on
  done/error/abort
- Smooth scroll needs the report container to be scrollable; if the
  parent has `overflow: auto`, anchors work natively. Verify in the
  current ResearchMode container — may need a small CSS tweak
- The Retry button must reuse the same question. Keep the question in
  state through the error path; don't clear it on `phase: "error"`

## Out of scope
- Backend changes (M2 already handles cancel server-side)
- The Playwright spec asserting all of this (M5)
- Source snippets in the `## Sources Used` section — open question,
  decided in this milestone but implementation is title-only for v1
- Non-text export formats (PDF, HTML)

## Verification
- Manual: run a real question; click each `[N]` link, confirm smooth
  scroll to the matching source
- Manual: start a run, click Cancel mid-stream, confirm the phase chip
  resets and the submit button re-enables; check Ollama logs show the
  generation cancelled (server-side from M2)
- Manual: stop Ollama (`pkill ollama`), submit a question, confirm the
  error panel appears with a Retry button
- Manual: click Copy, paste somewhere, confirm full markdown text
- Manual: click Download, confirm a `.md` file appears in Downloads
  with sensible content
- `cd frontend && npx playwright test` exits 0 (25/25 existing tests)

## Risks
- Citation post-processing may double-wrap if the user re-runs without
  a fresh DOM mount — guard with a class check or run on the markdown
  source
- Copy on iOS/Safari requires a user-gesture context; should be fine
  inside the click handler. Document the limitation if it surfaces
- The error panel's "data.message" must be sanitised — never
  `dangerouslySetInnerHTML` it
