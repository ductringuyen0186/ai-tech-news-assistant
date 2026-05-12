# [Feature+Test] framer-motion polish + per-tab Playwright smoke + demo video

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature + Test                                                         |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, motion, tests, validation                                    |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 6           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
Final milestone. Polish the motion across the app with `framer-motion`. Add per-tab Playwright happy-path smoke. Capture a demo video. This is the mission's closing argument — proof that the whole thing works and looks coherent.

## Description

### Part A — framer-motion polish

1. Install `framer-motion`
2. Animate the following:
   - Subagents panel rows enter/exit with stagger (50ms between rows; spring effect)
   - Subagents panel collapse/expand: smooth height transition
   - Citation hover card pop: scale + opacity spring
   - Suggested-query chips: stagger on appearance (~30ms between chips)
   - Suggested follow-up chips after report: same stagger
   - Sub-questions panel rows (from M2): subtle slide-in as they fire
   - Page tab transitions on sidebar click: cross-fade (200ms)
   - Save button on research report: scale-up tap; flip to "Saved ✓"
3. Performance: every animation under 300ms. No spring-bouncing for layout-critical elements (jitter is worse than static)
4. Respect `prefers-reduced-motion`: when the OS reports reduced motion, ALL framer-motion animations resolve to instant (use `useReducedMotion` hook)

### Part B — Per-tab Playwright happy-path smoke

Each tab gets ONE end-to-end test that drives a user-realistic interaction and asserts core success:

| Tab | Happy path | Core assertion |
|---|---|---|
| News Feed | Type in search, filter chip, click article | Article opens; trending rail visible |
| Research | Click suggested chip, wait for done | Report renders; table elements present (for the table-test); ≥1 citation; ≥3 follow-ups |
| Knowledge Graph | Navigate; hover an entity | Stat cards visible; ≥5 nodes on canvas |
| Digest | Navigate; see top stories | ≥3 top stories; trending topics row |
| Ask AI | Type question, get response | Response renders; ≥1 source visible |
| Settings | Toggle theme | `<html>` class flips; localStorage updated |
| Saved | Save research, navigate to Saved, open, delete | Full flow without errors |

These tests REUSE the existing per-tab specs (`news-feed.spec.ts`, `research.spec.ts`, etc.) and ADD the happy-path test alongside the existing rubric assertions.

### Part C — Per-tab visual baselines

For each tab's final state (after the happy path completes), capture a screenshot baseline:
- `frontend/e2e/__screenshots__/news-feed-final.png`
- `frontend/e2e/__screenshots__/research-final.png`
- ... etc

Use Playwright's `toHaveScreenshot()` with threshold=0.1 (10% pixel tolerance) so OS font-rendering differences don't flake. **Lock fonts to system stack** in CSS so all developers / CI machines see the same fonts.

The maintainer eyeballs the screenshots ONCE and commits the baselines. From then on, any visual change triggers a Playwright failure that surfaces the diff.

### Part D — Demo video

After all per-tab smoke tests pass, record ONE comprehensive 2-3 minute demo:
1. Open app (dark theme by default)
2. Cmd+K palette → search → open Research
3. Click a suggested query → watch the agent work end-to-end
4. Sub-questions panel appears (within 5s)
5. Subagents panel fills (≤4 in flight at a time)
6. Synthesis tokens stream
7. Final report includes a rendered table (the M2 bug fix)
8. Click a `[N]` citation → hover card shows article preview
9. Click Save → check Saved tab → open saved report
10. Click a follow-up suggestion → another run starts (cancel mid-way)
11. Toggle theme to light in Settings → reload → still light
12. Navigate to all other tabs briefly

Save as `docs/demos/mission-3-final.webm` (Playwright's built-in video output is webm by default).

## Acceptance criteria
- [ ] `framer-motion` installed and pinned
- [ ] Subagent rows animate on enter/exit with stagger
- [ ] Citation hover card pops with scale + opacity
- [ ] Suggested chips stagger on appearance
- [ ] Page tab transitions cross-fade
- [ ] `useReducedMotion` honored throughout
- [ ] Per-tab happy-path tests exist (7 tabs covered including Saved)
- [ ] Per-tab visual baseline screenshots committed
- [ ] `toHaveScreenshot` assertions pass with threshold=0.1
- [ ] Demo video captured: `docs/demos/mission-3-final.webm` (2-3 min)
- [ ] All 35 existing Playwright tests still pass
- [ ] No `console.error` during any test
- [ ] Bundle: framer-motion ≤ 25KB gzipped (verify in Vite build report)

## Implementation notes
Files:
- `frontend/package.json` — add `framer-motion`
- `frontend/src/components/SubagentsPanel.tsx` (or inline in ResearchMode) — AnimatePresence + motion.li for stagger
- `frontend/src/components/CitationHoverCard.tsx` — motion.div with spring
- `frontend/src/components/SuggestedQueries.tsx` — stagger children
- `frontend/src/components/ResearchProgressTimeline.tsx` (from M2) — entry transitions
- `frontend/src/components/Sidebar.tsx` — page tab cross-fade
- `frontend/playwright.config.ts` — ensure video capture is `on`, screenshot threshold configured
- `frontend/e2e/*.spec.ts` — add happy-path tests + screenshot baseline assertions
- `frontend/e2e/__screenshots__/` — NEW directory; baselines committed
- `docs/demos/mission-3-final.webm` — NEW (Playwright artifact)

Gotchas:
- `AnimatePresence` requires a unique `key` per child. Use `(skill, article_id)` as the key on subagent rows
- Stagger via `staggerChildren` on a parent `motion.ul`, NOT via per-child delays (cleaner code)
- Visual baselines flake on font rendering across OS. Lock to system fonts: `font-family: ui-sans-serif, system-ui, ...`
- Use Playwright's `--update-snapshots` flag once to capture initial baselines; commit them
- Demo video: use a single Playwright test that drives the full flow; Playwright's `video: 'on'` will capture it. Rename and move the artifact to `docs/demos/`

## Out of scope
- Performance optimization (lazy-load tabs, code splitting)
- Storybook stories per component
- Per-component visual baselines (just per-tab final states)

## Verification
- `cd frontend && npx playwright test` — full suite green; new per-tab tests included
- `cd frontend && npx playwright test --update-snapshots` — regenerates baselines (one-time)
- Open `docs/demos/mission-3-final.webm` — verify it shows the full flow

## Risks
- `framer-motion` AnimatePresence + React Strict Mode in dev can double-mount components; verify animations don't double-fire
- Visual baselines committed to git inflate the repo. Acceptable for a portfolio; consider Git LFS if it grows
- Demo video at slowMo=600 (per playwright.config.ts) might be too slow — record at slowMo=0 for a tight final demo

## Mission completion criteria
After this milestone:
- All 6 milestones marked complete
- All 35+ existing Playwright tests green
- 7 per-tab happy-path tests added (+ visual baselines)
- Demo video captured and archived
- Final mission report written at `docs/missions/ui-polish-report.md`
