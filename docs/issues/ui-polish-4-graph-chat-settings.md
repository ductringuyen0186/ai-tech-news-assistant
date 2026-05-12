# [Feature] Knowledge Graph + Ask AI + Settings polish

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, knowledge-graph, chat, settings                              |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 4           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
The remaining 3 tabs get the design language. Ask AI also gets citation hover cards (the third Round-1 engagement feature). Settings adds theme + density toggles.

## Description

### Knowledge Graph
1. Canvas: dark background matching theme tokens, nodes use accent color for highlight, edge lines softer/lower contrast
2. Stat cards above the graph: Linear-dense, status-color counts (entities, mentions, top entity)
3. Empty state if no entities yet — friendly text + "Run ingestion" hint

### Ask AI (Chat)
1. Citation hover cards on `[N]` markers in RAG responses. Component: `CitationHoverCard.tsx` (NEW or reused if shared with Research)
2. Hovering for ≥200ms on `a.citation` fetches `/api/news/{article_id}` once per session (Map cache); renders a 300px-wide card with title + source + summary preview + publish date
3. Card auto-positions near cursor; arrow points back at link; Esc / mouse-leave closes
4. Apply density preset to message bubbles

### Settings
1. Theme toggle: dark / light radio group. Persists via the M1 `localStorage.techpulse-theme` mechanism
2. Density toggle UI: compact / comfortable radio group. Persists in localStorage. **Behavior deferred** — the radio writes the value but doesn't currently change the layout (v2). Document this in a tooltip / muted text
3. Existing settings (RSS sources, ingest schedule, etc.) reformatted to the dense layout

## Acceptance criteria
- [ ] Knowledge Graph canvas uses theme tokens (dark + light both render)
- [ ] Stat cards use the new design language
- [ ] Empty state if no entities — descriptive, not blank
- [ ] `CitationHoverCard.tsx` exists; hovering a `[N]` on Ask AI for 200ms+ shows card
- [ ] Card includes title + source + summary preview + publish date
- [ ] Card uses Map cache for `/api/news/{id}` (no duplicate fetches)
- [ ] Settings has theme toggle (works) + density toggle (UI only, with deferred-behavior note)
- [ ] Existing `knowledge-graph.spec.ts` + `chat.spec.ts` + `settings.spec.ts` tests pass
- [ ] New tests: hover card on chat citation, theme toggle in Settings flips class
- [ ] If Research tab also has citation hover cards (carryover from earlier work), reuse the same component

## Implementation notes
Files:
- `frontend/src/components/KnowledgeGraph.tsx` — reskin
- `frontend/src/components/ChatInterface.tsx` — citation hover cards on RAG responses
- `frontend/src/components/Settings.tsx` — theme + density toggles
- `frontend/src/components/CitationHoverCard.tsx` — NEW (or shared if Research tab already added in earlier work)
- `frontend/e2e/knowledge-graph.spec.ts` — reskin assertions
- `frontend/e2e/chat.spec.ts` — hover card assertion
- `frontend/e2e/settings.spec.ts` — theme toggle assertion

Gotchas:
- The graph canvas is likely a `<canvas>` element with manual draw. Verify dark mode by checking the canvas's actual fill colors after re-render, not just the surrounding container
- Hover cards must not block the cursor — use `pointer-events: none` on the card so the user can click through to the link if they want
- Density toggle UI only: store the choice in `localStorage.techpulse-density` so v2 can read it later

## Out of scope
- Saved Research (M5)
- framer-motion polish (M6)
- LLM-driven follow-up suggestions (M5)

## Verification
- `cd frontend && npx playwright test knowledge-graph.spec.ts chat.spec.ts settings.spec.ts` — all pass
- Manual: hover citations on Ask AI tab — card appears within 200ms
- Manual: toggle theme in Settings — `<html class="dark">` flips; reload preserves

## Risks
- Citation hover card can race with the M4 click-to-scroll behavior — ensure hover does NOT navigate; only click does
- The graph's existing tests assert specific node count / labels — preserve those selectors during reskin
