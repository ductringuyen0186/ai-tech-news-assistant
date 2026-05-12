# [Feature+Bugfix] Markdown migration + Research agent responsiveness UX

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature + Bugfix                                                       |
| Priority       | P0                                                                     |
| Estimate       | L (~1.5-2 days — heaviest M3 milestone)                                |
| Assignee       | unassigned                                                             |
| Labels         | frontend, backend, markdown, research, streaming-ux                    |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 2           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
Two problems on the Research tab:

1. **Markdown table bug** (from the user's screenshot): the M3 inline markdown renderer doesn't handle GFM tables. The agent's `| Company | Amount |` markdown renders as raw pipes and dashes.

2. **The agent "feels" unresponsive**: today the user clicks Research and waits 30-60+ seconds staring at phase chips and "running" badges before ANY content appears. Then tokens stream. This is the architecture working correctly, but the UX is mute. The user wants the agent to feel responsive throughout — stream what it's "thinking" as it works, similar to how Claude/ChatGPT surface tool use inline.

This milestone fixes both.

## Description

### Part A — Markdown rendering (the bug fix)

1. Install `react-markdown` + `remark-gfm`
2. New `frontend/src/components/MarkdownReport.tsx`:
   - Uses `react-markdown` with `remarkPlugins={[remarkGfm]}`
   - `components` override for `code`, `a` (citation linkifier preserved), `table`, `th`, `td`
   - Citation post-processing as a render-time AST walk (NOT a string replace)
   - Accepts `text: string` and `linkifyCitations: boolean` props
   - NO `rehype-raw` (security)
3. `ResearchMode.tsx` + `ChatInterface.tsx` switch to `MarkdownReport`
4. Delete the ~150-line M3 inline renderer

### Part B — Agent responsiveness UX (the big one)

The current SSE stream emits:
```
phase: Decomposing
phase: Searching (1/N)
phase: Searching (2/N)
...
subagent: start (skill, article_id)
subagent: done (skill, article_id, duration_ms)
...
phase: Synthesizing
phase: token (chunk) × N
phase: done (report)
```

The user sees: phase chip cycling + subagent rows lighting up. NO actual content until synthesis tokens stream.

**After this milestone**, the SSE stream is enriched and the UI surfaces intermediate content immediately:

**Backend changes** (small, additive — keep backward compat):
1. After decomposition, emit a NEW event:
   ```json
   {"type": "decomposed", "sub_questions": ["What companies...", "How does...", ...]}
   ```
2. After each search, emit a NEW event with the resulting article previews:
   ```json
   {"type": "search_results", "sub_question_index": 0, "articles": [{"id": 42, "title": "...", "source": "TechCrunch"}, ...]}
   ```
3. Enrich the `subagent: done` event to include the per-article summary text:
   ```json
   {"type": "subagent", "data": "done", "skill": "summarize_article", "article_id": 42, "duration_ms": 4728, "summary": "First 280 chars of the per-article summary..."}
   ```
   (Truncate to 280 chars so the SSE frame stays small.)

**Frontend changes**:
1. **Sub-questions panel**: when `decomposed` event arrives, show the 3-5 sub-questions as a numbered list above the Subagents panel. Each sub-question has its own progress indicator (pending → in-progress when its search starts → done when its subagents finish)
2. **Live article reading panel**: when `search_results` events arrive, show the article titles being read for each sub-question. Each title is a hover-card target (M4 work — for now, just show title + source)
3. **Expandable subagent rows**: each `subagent: done` row in the Subagents panel becomes EXPANDABLE. Click to reveal the per-article summary inline (the truncated 280 chars from the SSE event, plus a "read full" link to the article URL)
4. **Phase chip strip → vertical progress timeline** below the input:
   ```
   ● Decomposing — done (2.1s)
   ● Searching (4/4 sub-questions) — done (6.3s)
   ● Reading 12 articles (4 in flight, 8 done) — 18.4s elapsed
   ○ Synthesizing — waiting
   ○ Done
   ```
   Replaces the single phase chip with a richer vertical timeline. Each row has elapsed time + status.

5. **Suggested-query chips** on empty state (4-6 curated queries: "OpenAI's last 30 days", "AI chip market shifts", "Anthropic vs OpenAI", etc.)

### Part C — Time-to-first-content target

The architectural metric this milestone enforces:
- **Today**: Time from Submit to first content visible to user: ~10-15s (just phase chip text changing)
- **Target after this milestone**: Time from Submit to substantive content: **≤ 5s** (sub-questions render as soon as decompose completes)
- **Time to first article summary visible**: ≤ 15s (first subagent done → expandable row shows summary)

## Acceptance criteria

### Markdown
- [ ] `react-markdown` + `remark-gfm` installed and pinned
- [ ] `MarkdownReport.tsx` exists; used by ResearchMode + ChatInterface
- [ ] The exact markdown from the user's screenshot renders as a proper `<table>` with `<th>` + `<td>`
- [ ] Citation `[N]` markers still render as `<a class="citation" href="#source-N">[N]</a>`
- [ ] Code blocks render with monospace + background
- [ ] No `rehype-raw` is used

### Backend SSE enrichment
- [ ] `AgenticResearchService.run()` emits a `decomposed` event after decomposition with `sub_questions: string[]`
- [ ] After each sub-question's search, emits `search_results` event with the article preview list (id, title, source)
- [ ] `subagent: done` event includes a `summary` field (first 280 chars of the per-article summary)
- [ ] M2 backend integration tests in `test_research_sse.py` cover the new event types
- [ ] Live tests in `test_research_live.py` assert the new events appear in the stream

### Frontend UX
- [ ] Empty Research tab shows 4-6 suggested-query chips
- [ ] On click, chip fills input and submits
- [ ] Sub-questions panel renders when `decomposed` event arrives (within 5s of submit, verified)
- [ ] Live article reading panel shows article titles per sub-question as searches complete
- [ ] Subagent rows are EXPANDABLE — click reveals the per-article summary preview
- [ ] Phase progress is a vertical timeline (5 rows: Decomposing, Searching, Reading articles, Synthesizing, Done) with elapsed time + status
- [ ] The single-chip phase indicator is replaced by the timeline

### Tests
- [ ] All 6 existing `research.spec.ts` tests still pass
- [ ] New mock SSE bodies in `research.spec.ts` include the 3 new event types (decomposed, search_results, enriched subagent:done)
- [ ] New Playwright test: markdown table from the user's screenshot renders as `<table>` element
- [ ] New Playwright test: sub-questions panel renders ≥3 sub-questions when decomposed event arrives
- [ ] New Playwright test: subagent row expands to show summary
- [ ] All 17 existing backend contract tests still pass
- [ ] All 6 SSE integration tests still pass (new events are additive)

### Performance
- [ ] Time-to-sub-questions-visible ≤ 5s (verified live)
- [ ] Time-to-first-article-summary-visible ≤ 20s (live)

## Implementation notes

Files:
- `frontend/package.json` — add `react-markdown`, `remark-gfm`
- `frontend/src/components/MarkdownReport.tsx` — NEW
- `frontend/src/components/SuggestedQueries.tsx` — NEW
- `frontend/src/components/SubQuestionsPanel.tsx` — NEW (the live progress + reading list)
- `frontend/src/components/ResearchProgressTimeline.tsx` — NEW (vertical timeline)
- `frontend/src/components/ResearchMode.tsx` — heavy refactor: drop inline markdown, drop single-chip indicator, add the new components
- `frontend/e2e/research.spec.ts` — update mock SSE bodies + add new tests
- `backend/src/services/agentic_research_service.py` — emit `decomposed` event; emit `search_results` after each search; enrich `subagent: done` with summary text
- `backend/tests/integration/test_research_sse.py` — assert new events
- `backend/tests/integration/test_research_live.py` — assert new events in live stream

Gotchas:
- The `decomposed` event MUST be emitted before any `Searching` phase event so the frontend can pre-render the sub-question slots
- The `subagent: done` summary truncation (280 chars) keeps the SSE frame small. Don't send the full summary — the frontend already has `/api/news/{id}` for the full version if it wants
- The expandable row state must reset between research runs (same as Subagents panel state)
- Backward compat: the existing `phase` events MUST still fire in the same sequence so frontend code that doesn't yet handle the new events still works. The new events are PURELY ADDITIVE
- The vertical timeline replaces the single phase chip but PRESERVES the `data-testid="research-phase-chip"` selector — wrap the timeline's current step indicator with that testid so existing M2.M5 + M4 tests still find it
- OneDrive sync truncation is real; verify with `tail -30` after every edit to large files

## Out of scope
- LLM-driven follow-up suggestions (M5 will add 3 follow-ups under the report — keep that scope separate)
- Saved Research (M5)
- Hover cards on citations (M4)
- framer-motion animations (M6 will polish the entries/exits — for now, plain CSS transitions are fine)

## Verification
- `cd backend && pytest tests/integration/test_research_sse.py tests/integration/test_research_live.py -v` — all pass with new event assertions
- `cd frontend && npx playwright test research.spec.ts` — all 6 existing + new tests pass
- Manual: submit a real query, time-to-first-sub-question and time-to-first-summary visible — verify against the perf targets

## Risks
- Adding 3 new event types is the largest backward-compat surface area in this mission. Frontend mocks must be updated AND the existing M2/M5 tests must continue to pass — test carefully
- The expandable row UI competes with the auto-expand-on-first-event behavior from M5. Verify the M5 test still passes
- Backend emitting `decomposed` event MIGHT race with the orchestrator's own internal state. Make sure the event is emitted AFTER the JSON parse succeeds (so the sub-questions list is final) but BEFORE the first search starts
