# [Feature] Render Subagents panel showing per-article progress

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, ux, sse, telemetry                                           |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 5 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
With M4 emitting `subagent` events, M5 surfaces them in the UI. The user gets to *see* the multi-agent architecture: a panel below the phase chip that lights up per article — "Summarizing article 12 (running)", "Summarizing article 7 (done, 4.3s)", etc. This is the visible portfolio payoff.

## Description
**Today (after M4):** The backend emits `subagent: start|done|error` events with `skill`, `article_id`, `duration_ms`, `message` fields. The frontend's SSE parser ignores them (they don't match `type === "phase" | "token" | "error"`).

**After this change:** `ResearchMode.tsx` is extended:

1. The SSE parser handles `type: "subagent"` events. Each event updates a state map keyed by `(skill, article_id)`:
   - `start` → row added with status: "running", startedAt: now
   - `done` → row's status: "done", durationMs: event.duration_ms
   - `error` → row's status: "error", message: event.message
2. A new collapsible "Subagents" panel renders BELOW the phase chip and ABOVE the report body
3. Panel header: "Subagents (N running, M done, K errored)" with a chevron toggle
4. Panel rows: skill name (icon + label), article ID, status badge, duration (when done) or "running…" (when in flight) or error message (when failed)
5. Panel default state: auto-expand on first `subagent: start` event; user can collapse manually
6. Panel resets between runs (cleared on a new submit)
7. New `data-testid` hooks: `research-subagents-panel`, `research-subagents-row` (one per row)

## Acceptance criteria
- [ ] `ResearchMode.tsx` parses `type: "subagent"` events and tracks them in state
- [ ] A collapsible `<Collapsible>` panel (using existing shadcn/ui primitives) renders below the phase chip
- [ ] Panel header shows live counts: "N running, M done, K errored"
- [ ] Each row shows: skill name (e.g. "summarize_article"), article ID (e.g. "#42"), status badge, duration (when done)
- [ ] Panel auto-expands on first `subagent: start`
- [ ] Panel state resets when a new run starts (the user clicks Research again)
- [ ] `data-testid="research-subagents-panel"` on the panel root
- [ ] `data-testid="research-subagent-row"` on each row (multiple)
- [ ] All 5 existing `research.spec.ts` tests still pass after mock SSE bodies are updated to include sample subagent events
- [ ] One new test in `research.spec.ts` asserts: "Subagents panel renders ≥1 row when subagent events arrive". Uses the mock helper updated to inject 2-3 subagent events
- [ ] 8-category UX rubric still passes on the rendered Research surface (panel doesn't overflow, no console errors when rendering)

## Implementation notes
Files likely involved:
- `frontend/src/components/ResearchMode.tsx` — extend SSE parser + add the panel
- `frontend/e2e/research.spec.ts` — update mock SSE body to include subagent events; add new test asserting the panel renders rows

Gotchas:
- The existing Copy/Download buttons + cancel button must continue to work. Don't accidentally hide them by inserting the new panel in the wrong place
- The `subagent: error` event's `message` field could contain a long error string — truncate to 80 chars in the row display, with full text on hover (use `<span title={fullMessage}>...</span>`)
- The `(skill, article_id)` key handles deduplication if (somehow) the backend re-fires a start event for the same subagent
- Use the existing `Badge` component from `components/ui/badge.tsx` for the status indicator. Variant: secondary (running), default (done), destructive (error)
- Use `Collapsible` from `components/ui/collapsible.tsx` if it exists, else a simple `useState(true)` + chevron button
- The panel resets on submit by being driven from a state slot that's reset in the submit handler

## Out of scope
- Backend changes (M4 already emits subagent events)
- Ingestion migration (M6 owns that)
- Per-skill icon library (use plain text labels for now)
- Animated transitions on the rows (nice-to-have, skip)

## Verification
- Manual: type a question, watch the Subagents panel light up, see rows appear and complete
- `cd frontend && npx playwright test research.spec.ts` exits 0 with 6/6 tests green (5 existing + 1 new)
- DevTools Console: zero `console.error` during a successful run (rubric requirement)
- DevTools Network: SSE response contains `data: {"type": "subagent", ...}` lines

## Risks
- If `subagent: start` arrives but the matching `done`/`error` never does (e.g. backend bug or network drop), the row stays in "running" state forever. Acceptable for v1 — the cancel button or browser tab close clears it
- The panel adds vertical real estate; on smaller screens the report scrolls farther down. Acceptable; Research is desktop-first
- If the user fires many sequential queries quickly, the panel may accumulate rows from prior runs unless properly reset. Tested via the "panel state resets on new submit" assertion
