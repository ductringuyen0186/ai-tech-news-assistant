# PRD: UI polish — developer-dashboard rebuild

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Status         | Draft                                                                  |
| Author         | duc                                                                    |
| Owner          | duc                                                                    |
| Created        | 2026-05-08                                                             |
| Target ship    | 2026-05-15 (~7 days)                                                   |
| Design context | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Summary

Rebuild the TechPulse AI frontend to a **Vercel/Linear developer-dashboard
aesthetic** across all 6 tabs. Dark default theme + light option. Left
sidebar nav + Cmd+K command palette. Linear-dense typography and rows.
Replace the M3 inline markdown renderer with `react-markdown +
remark-gfm` (fixes the table-rendering bug from the user's screenshot).
Add three engagement features: suggested follow-up questions on completed
research reports, saved research with a backend table, and citation
hover cards. Animate transitions with `framer-motion`. Tightened
Playwright per-tab smoke + visual baselines as validation.

## Problem

Mission 2 made the architecture recruiter-worthy. The UI isn't. A
screenshot the user shared shows the agent's markdown table rendering
as `| Company | Amount |\n|---|---|\n| Pit | $9 million |` raw text —
the M3 inline markdown renderer doesn't handle GFM tables. Beyond that
single bug, the broader UI is shadcn-default: top tabs, light theme,
no power features, no engagement loops, no consistent polish across
tabs.

For a backend / infra / platform engineering recruiter, the first
impression is the UI. Today the UI looks like a basic CRUD app. After
this mission, it should look like a tool they'd actually use.

## Goals & non-goals

### Goals

- Left sidebar nav + Cmd+K command palette
- Dark default theme + light toggle, with FOUC-free initial render
- Linear-dense typography (13-14px body, 4-8px row padding)
- Single accent color (blue) + status palette (running/done/error)
- Markdown rendering via `react-markdown + remark-gfm` — tables, code,
  footnotes, task lists, strikethrough all render correctly
- Three engagement features:
  1. Suggested follow-up questions after a research report
  2. Saved research (backend `saved_research` table + sidebar entry)
  3. Citation hover cards (article preview on hover of `[N]`)
- framer-motion polish on subagents panel, hover cards, page tab
  transitions, suggested-query stagger
- Per-tab Playwright happy-path smoke + visually-approved screenshot
  baselines as validation
- All 6 tabs visually consistent (News Feed, Research, Knowledge Graph,
  Digest, Ask AI, Settings)
- Empty states: Research suggested queries + News Feed "Trending Now"
  rail
- 35 existing Playwright tests stay green; backend M2 tests stay green;
  live research test 3/3

### Non-goals

- Mobile / tablet / responsive design
- Touch interactions
- New tabs beyond Saved Research
- Server-side rendering / hydration optimization
- WCAG AA full audit (focus rings + basic keyboard nav only)
- Logo redesign / rebrand
- Lighthouse / performance budget tracking
- i18n / RTL
- Editing reports
- Share-by-URL for reports

## Users & use cases

### Primary user
Backend / infra / platform engineering recruiter, ~2-5 min portfolio
scan. First impression decides whether they read the code.

### Secondary user
The maintainer, using the app as a real news-research tool.
Keyboard-first (Cmd+K) + saved research = daily usable.

### Use cases

1. **Recruiter walkthrough** — opens app, sees dark sidebar nav with 6
   tabs + Saved entry, lands on Research (default), sees 4-6 suggested
   query chips, clicks one, watches the subagents panel animate as
   articles get summarized, reads a rendered table in the final report,
   hovers a `[N]` citation to see article preview, clicks "Save."
2. **Maintainer daily use** — Cmd+K, picks a recent research query,
   re-runs it, reviews + saves. Toggles theme via Settings.
3. **Recruiter judging code quality** — checks the new
   `MarkdownReport.tsx`, the `CommandPalette.tsx`, the
   `saved_research` backend table + endpoints + tests.

## Requirements

### Functional

- `App.tsx` rewritten to use sidebar layout. `ThemeProvider` +
  `CommandPaletteProvider`. Tab state still SPA, but sidebar drives it
- `Sidebar.tsx` — vertical 6 nav items + Saved entry + theme toggle at
  bottom. Active state highlighted with accent color
- `CommandPalette.tsx` — Cmd+K modal (Ctrl+K on Windows). Lists tabs +
  last-N research queries. Arrow keys + Enter navigate. Esc closes.
  Backdrop click closes
- Theme system — Tailwind dark mode (class strategy). `<html
  class="dark">` set by inline script in `index.html` before React
  mounts, reading `localStorage.techpulse-theme`. Default is `dark` if
  no preference set
- `MarkdownReport.tsx` — `react-markdown + remark-gfm`. Citation
  linkifier preserved (post-render pass replaces `[N]` plain text with
  anchor link to `#source-N`, OR remark plugin). NO `rehype-raw`
  (security)
- `SuggestedQueries.tsx` — accepts a `queries: string[]` prop. Renders
  chip row with hover/focus states. Click fires a callback (parent
  fills input + submits)
- Research tab empty state — show 4-6 hardcoded suggested queries
  (curated: "OpenAI funding past month", "AI chip market shifts",
  "Anthropic vs OpenAI announcements", etc.)
- After research completes — show 3 follow-up suggestions BELOW the
  report. Source: optional LLM call generating follow-ups, OR a
  template-based extractor pulling keywords from the report. Lean
  template-first for v1
- `SavedResearchList.tsx` — sidebar entry rendering list of saved
  reports. Each row: question + created_at + delete button. Click row
  to open the report
- Save button on a research report — POSTs to backend, updates UI
- Backend `saved_research` table:
  ```sql
  CREATE TABLE IF NOT EXISTS saved_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    report_md TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
  ```
- Backend endpoints:
  - `POST /api/saved-research` — body `{question, report_md, sources}` → returns `{id, created_at}`
  - `GET /api/saved-research` — list, ordered by created_at desc
  - `GET /api/saved-research/{id}` — single
  - `DELETE /api/saved-research/{id}` — remove
- `CitationHoverCard.tsx` — fires on hover of `a.citation` for 200ms+.
  Fetches `/api/news/{article_id}` once per article ID per session
  (Map cache). Positions card near cursor; arrow points back at link
- News Feed — Trending Now rail at top (top 3-5 categories by article
  count this week). Article cards linear-dense
- Knowledge Graph — reskinned canvas + stat cards. Empty state if no
  entities
- Ask AI — citation hover cards on RAG responses (reuse the component)
- Settings — theme toggle (light/dark), density toggle (compact/
  comfortable, behavior deferred — UI affordance only)

### Non-functional

- **Performance**: cold load TTI ≤ 3s on the maintainer's dev machine.
  Theme-flash budget: 0ms (FOUC-free init)
- **Bundle**: framer-motion ≤ 25KB gzipped. react-markdown + remark-gfm
  ≤ 35KB gzipped combined. Total acceptable bundle growth ≤ 80KB
- **A11y**: focus rings visible on all interactive elements. Keyboard
  nav on Cmd+K palette. Semantic HTML (role="tablist" for sidebar
  preserved so Playwright selectors keep working)
- **Compatibility**: latest 2 versions of Chrome / Firefox / Safari
- **Tests**: 35 existing Playwright tests stay green. M2 backend
  contract tests stay green. New tests per tab (7 specs, 1 per
  visible surface)

## Success metrics

### Acceptance (must hold)

- Markdown table from the user's screenshot renders as a proper HTML
  table with borders and aligned columns
- Cmd+K opens the palette from any tab; arrow + Enter navigates; Esc
  closes; no console errors
- Dark mode persists across reload via localStorage. Light mode works
  fully. NO theme flash on initial load
- Suggested-query chip click → input filled + research run
- 3 follow-up suggestions appear under every completed research report
- Save button on report → POST → appears in Saved list → click in
  Saved → renders saved report → Delete → removes
- Citation hover card appears within 200ms; article title + source +
  summary + date visible
- All 6 tabs visually consistent: same sidebar, same typography, same
  color tokens

### Rollback criteria (any one triggers a revert)

- Playwright suite drops below 90% pass rate after the migration
- Bundle size grows by more than 100KB gzipped
- Cold load TTI breaches 5s
- The original M2 architecture (subagents panel, phase chip, SSE
  stream) breaks in any visible way
- Backend `saved_research` migration corrupts existing news.db

## Rollout plan

Direct cutover. The sidebar rebuild touches App.tsx — there's no
gradual rollout possible without forking the route tree. Ship the
mission as a single coordinated set of commits, validate, then move on.

1. **Day 1-2** — M1: design system foundation (sidebar nav, theme
   provider, Cmd+K palette, typography refresh)
2. **Day 3** — M2: markdown rendering migration + Research tab polish
3. **Day 4** — M3: News Feed + Digest tabs polish
4. **Day 5** — M4: Knowledge Graph + Ask AI + Settings tabs polish
5. **Day 5-6** — M5: saved research (backend + frontend)
6. **Day 6-7** — M6: framer-motion polish + per-tab Playwright smoke +
   final demo video

## Milestones & validation contracts

### Milestone 1 — Design system foundation *(L, ~2 days)*

**Goal.** Sidebar nav, dark theme, Cmd+K palette, typography refresh.
No content changes yet — just the chrome.

**Validation contract:**
- Sidebar nav renders on every tab with 6 entries + Saved + theme toggle
- Dark theme is the default; light toggle works; FOUC-free init
- Cmd+K opens palette; arrow keys + Enter navigate; Esc closes
- All 35 existing Playwright tests still pass (selectors preserved via
  `role="tab"` + `role="tablist"` on sidebar items)
- Tailwind config has dark mode class strategy + new semantic colors
- New tests: `frontend/e2e/sidebar.spec.ts` covers nav, theme toggle,
  Cmd+K open/close/navigate

### Milestone 2 — Markdown rendering + Research tab polish *(M, ~1 day)*

**Goal.** Fix the markdown table bug. Polish Research tab to showcase
quality.

**Validation contract:**
- `react-markdown + remark-gfm` installed and pinned
- `MarkdownReport.tsx` exists, used by ResearchMode + ChatInterface
- The exact markdown from the user's screenshot renders as a proper
  HTML table (test verifies `<table>` + `<th>` + `<td>` elements)
- Citation `[N]` linkifier preserved — anchors still target
  `#source-N`, M4 hover behavior still works
- All 6 existing `research.spec.ts` tests still pass
- New test: table rendering assertion using the user's exact markdown

### Milestone 3 — News Feed + Digest polish *(M, ~1 day)*

**Goal.** Two discovery surfaces get the design language.

**Validation contract:**
- News Feed top: "Trending Now" rail with 3-5 categories. Hover state
- Linear-dense article card layout (13px body, 4px row padding)
- Digest top stories: status-colored chips, linear-dense
- All existing `news-feed.spec.ts` + `digest.spec.ts` tests pass
- New assertions: trending rail visible, dense layout

### Milestone 4 — Knowledge Graph + Ask AI + Settings polish *(M, ~1 day)*

**Goal.** Remaining 3 tabs get the design language.

**Validation contract:**
- Knowledge Graph: reskinned canvas (dark background), stat cards
  match the design tokens, empty state if no entities
- Ask AI: citation hover cards on RAG responses (reuse component)
- Settings: theme toggle, density toggle UI (behavior deferred)
- All existing `knowledge-graph.spec.ts` + `chat.spec.ts` +
  `settings.spec.ts` tests pass

### Milestone 5 — Saved research (backend + frontend) *(M, ~1 day)*

**Goal.** New backend table + endpoints + sidebar entry + save button.

**Validation contract:**
- `saved_research` table created via init_db; IF NOT EXISTS guard
  works against existing news.db
- 4 endpoints (POST, GET, GET-by-id, DELETE) with unit tests
- Frontend Save button on research reports works (POSTs, shows
  confirmation)
- Saved sidebar entry lists prior reports; click opens; delete removes
- New `saved-research.spec.ts` Playwright covers the full flow

### Milestone 6 — framer-motion + per-tab Playwright smoke + demo video *(M, ~1 day)*

**Goal.** Animation polish + visual baselines + demo proof.

**Validation contract:**
- framer-motion installed and pinned
- Subagent rows enter/exit with stagger; panel collapse animates;
  citation hover-card pops with spring
- Suggested-query chips stagger on appearance
- Per-tab final-state screenshot saved as Playwright visual baseline
- All 35 existing + new Playwright tests pass
- 2-3 min demo video recorded by Playwright, archived to
  `docs/demos/mission-3-final.webm`

## Dependencies

- **External (new)**: `react-markdown`, `remark-gfm`, `framer-motion`,
  `cmdk` (Cmd+K palette UI primitive)
- **Internal**: M2's `AgenticResearchService`, M5's Subagents panel,
  the existing M2 frontend hooks. All untouched at the API layer

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Sidebar rewrite breaks 35 existing Playwright selectors | Med | High | Preserve `role="tab"` on sidebar items, keep `role="tablist"` on the wrapper. Run existing suite after every M1 commit |
| react-markdown strips citation classes | Med | High | Citation linkifier becomes a remark plugin OR post-render walk. Tested against the user's exact table markdown |
| framer-motion bloats bundle | Low | Med | Tree-shake imports; verify in Vite build report. Budget 25KB |
| Cmd+K hotkey conflicts with browser | Low | Low | Use Cmd+K on macOS, Ctrl+K on Win/Linux. Test in DevTools |
| FOUC on theme load | Med | Med | Inline script in index.html sets `<html class="dark">` before React mounts |
| Saved research migration breaks existing news.db | Low | High | `CREATE TABLE IF NOT EXISTS`. Run against fresh + existing DBs as unit tests |
| Visual baselines flake on font rendering | Med | Med | Lock fonts to system stack; Playwright threshold 0.1; baseline approved once |
| 7-day timeline slips | Med | Low | Milestones are independently shippable. M6's video is the only one that depends on everything else |
| Density toggle in Settings ships UI without behavior | Low | Low | Document clearly as v2 follow-up. Setting persists in localStorage but doesn't drive layout yet |

## Open questions

- Cmd+K recents source: backend `saved_research` joined with a
  user-session table, OR localStorage cache. Lean localStorage for v1
- Follow-up suggestion source: LLM call (richer, slower) vs
  template-based (faster, dumber). Lean template for v1; M6 can flip
  to LLM if quality is bad
- Density toggle: ship UI only or wire behavior? Lean UI only
- Saved research max count: cap at N=100 to avoid table bloat? v2

## Appendix

- **Source design context**: [docs/designs/ui-polish.md](../designs/ui-polish.md)
- **Predecessor mission**: [docs/missions/per-article-subagents-report.md](../missions/per-article-subagents-report.md)
- **Existing E2E baseline**: 35 Playwright + 19 unit/integration + 3 live, all green at commit `2fdd2ce`
