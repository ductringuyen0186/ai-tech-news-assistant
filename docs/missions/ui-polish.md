# Mission: UI polish — developer-dashboard rebuild

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Status         | **Phase 1 complete — awaiting Phase 2 approval**               |
| Owner          | duc (orchestrator)                                             |
| Created        | 2026-05-08                                                     |
| Target ship    | 2026-05-15 (~7 days)                                           |
| Design context | [docs/designs/ui-polish.md](../designs/ui-polish.md)           |
| PRD            | [docs/prds/ui-polish.md](../prds/ui-polish.md)                 |
| Skill          | [missions](../../.claude/skills/missions/SKILL.md)             |

This mission rebuilds the TechPulse AI frontend to a **Vercel/Linear developer-dashboard aesthetic** across all 6 tabs. Dark default. Sidebar nav. Cmd+K palette. Linear-dense typography. Markdown table bug fixed via `react-markdown + remark-gfm`. Three engagement features: suggested follow-ups, saved research (backend-persisted), citation hover cards. **Plus**: research agent streaming UX so the user sees content within 5s of submit (sub-questions immediately, per-article summaries as they finish, not 30+s of mute phase chips).

It is broken into 6 milestones, each with its own ticketable issue. The orchestrator (this Claude session) spawns one worker subagent per milestone serially, then Scrutiny + (for UI milestones) User-Testing validators in parallel. Retry budget ≤ 3 per milestone.

---

## Milestones (in order)

### M1 — Design system foundation *(L, ~2 days)*
- **Issue:** [docs/issues/ui-polish-1-design-system.md](../issues/ui-polish-1-design-system.md)
- **Goal:** Sidebar nav, dark theme, Cmd+K palette, typography. No tab content changes yet — just the chrome.
- **Validation contract (top 3):**
  1. Sidebar renders 6 tabs + Saved + theme toggle; sidebar items have `role="tab"` so 35 existing Playwright tests stay green
  2. Dark theme default + light option; FOUC-free init via inline `<script>` in `index.html`
  3. Cmd+K opens palette; arrow keys + Enter navigate; Esc closes. New `sidebar.spec.ts` test

### M2 — Markdown migration + Research agent responsiveness UX *(L, ~1.5-2 days)*
- **Issue:** [docs/issues/ui-polish-2-markdown-and-research.md](../issues/ui-polish-2-markdown-and-research.md)
- **Goal:** Fix the table rendering bug AND make the agent feel responsive (sub-questions inline, per-article summaries as they finish, vertical progress timeline)
- **Validation contract (top 3):**
  1. Markdown from the user's screenshot renders as proper `<table>` element
  2. Backend emits new `decomposed` + `search_results` events + enriched `subagent: done` (with summary preview); frontend renders sub-questions panel + expandable subagent rows
  3. Time-to-sub-questions-visible ≤ 5s after submit (live test asserts this)

### M3 — News Feed + Digest polish *(M, ~1 day)*
- **Issue:** [docs/issues/ui-polish-3-newsfeed-and-digest.md](../issues/ui-polish-3-newsfeed-and-digest.md)
- **Goal:** Trending Now rail on News Feed; Linear-dense layout on both tabs
- **Validation contract (top 3):**
  1. Trending Now rail with ≥3 category items at top of News Feed
  2. Linear-dense rows (≤14px body, ≤8px padding) — verified via Playwright CSS assertions
  3. All existing `news-feed.spec.ts` + `digest.spec.ts` tests pass

### M4 — Knowledge Graph + Ask AI + Settings polish *(M, ~1 day)*
- **Issue:** [docs/issues/ui-polish-4-graph-chat-settings.md](../issues/ui-polish-4-graph-chat-settings.md)
- **Goal:** Reskin remaining 3 tabs; citation hover cards on Ask AI; theme + density toggles in Settings
- **Validation contract (top 3):**
  1. Knowledge Graph canvas + stat cards use theme tokens (dark + light)
  2. Citation hover card appears within 200ms on Ask AI; renders title + source + summary + date
  3. Settings theme toggle flips `<html>` class and persists in localStorage

### M5 — Saved research (backend + frontend) + follow-up suggestions *(M, ~1 day)*
- **Issue:** [docs/issues/ui-polish-5-saved-research-and-follow-ups.md](../issues/ui-polish-5-saved-research-and-follow-ups.md)
- **Goal:** `saved_research` SQLite table + 4 REST endpoints + frontend Save button + Saved sidebar tab + 3 follow-up chips after every report
- **Validation contract (top 3):**
  1. 4 endpoints (POST/GET/GET-by-id/DELETE) with unit tests; works on fresh AND existing news.db
  2. Save → list → open → delete flow in `saved-research.spec.ts`
  3. ≥3 follow-up suggestions rendered after every completed research report

### M6 — framer-motion + per-tab Playwright + demo video *(M, ~1 day)*
- **Issue:** [docs/issues/ui-polish-6-motion-and-validation.md](../issues/ui-polish-6-motion-and-validation.md)
- **Goal:** Animation polish, per-tab happy-path tests, visual baselines, 2-3 min demo video
- **Validation contract (top 3):**
  1. Subagent rows + citation hover cards + suggested chips animate via framer-motion; `useReducedMotion` honored
  2. 7 per-tab happy-path tests + visual baseline screenshots committed
  3. `docs/demos/mission-3-final.webm` captured and shows the full flow

---

## Estimated wall-clock & subagent budget

- **Workers:** 6 (one per milestone, serial)
- **Validators:** ~10 (Scrutiny per milestone + User-Testing for UI milestones M1, M2, M5, M6)
- **Retry budget:** ≤3 per milestone
- **Realistic worker count if retries hit:** 6–18
- **Wall-clock estimate:** ~7 days (1 week, focused scope)

## Kill-switch / rollback criteria

Mission stops and surfaces to the user if any of these hit:

- Any single milestone fails 3 worker attempts in a row
- Playwright suite drops below 90% pass rate after a migration
- Bundle size grows by > 100 KB gzipped
- Cold load TTI breaches 5s on the maintainer's dev machine
- The M2 agentic research flow (subagents panel, phase chip, SSE stream) breaks visibly
- Backend `saved_research` migration corrupts an existing news.db
- M2's time-to-sub-questions metric breaches 10s on a typical query

## Out-of-scope reminders (from PRD)

- Mobile / tablet / responsive
- New tabs beyond Saved
- WCAG AA full audit
- Logo redesign
- Lighthouse / performance budget
- i18n / RTL
- Editing reports
- Share-by-URL

---

## Mission state log

### 2026-05-08 — Phase 1 complete
- Design context written: `docs/designs/ui-polish.md` (12-of-12 user answers locked across 3 grill rounds)
- PRD written: `docs/prds/ui-polish.md` (6 milestones, ~7-day target)
- Six issue files written
- Mission plan written: this file
- **User added mid-grill**: research agent streaming UX (folded into M2 — sub-questions panel, per-article summary previews, vertical progress timeline)
- **Next step:** Phase 2 — surface plan to user and wait for explicit approval before spawning M1 worker

### Phase 3 log (to be filled in during execution)
_Each milestone appends a one-paragraph entry: worker commit SHA, validator verdicts, retries, learnings._

---

## How this mission was built

Daisy-chain pattern from `~/.claude/skills/missions/SKILL.md`:

1. `grill-me` — 3 rounds, 12 questions; user chose: all 6 tabs, desktop-only, Vercel/Linear style, sidebar + Cmd+K, Linear-dense, dark default, react-markdown + remark-gfm, backend-saved research, framer-motion, per-tab Playwright + visual baseline
2. Mid-grill enhancement: user added research-agent streaming UX as a separate concern → folded into M2's scope
3. `write-prd` — 6 milestones, validation contracts, risks
4. `write-issue` × 6 — per-milestone tickets
5. `missions` — this plan; will execute Phase 3 serially with adversarial validators after Phase 2 approval

## Predecessor missions

- [Agentic Research Mode](./agentic-research-report.md) — Mission 1, completed 2026-05-08
- [Per-article Subagents](./per-article-subagents-report.md) — Mission 2, completed 2026-05-08

Mission 3 builds on Mission 2's agent + subagents panel and makes both feel responsive AND look like a real product.
