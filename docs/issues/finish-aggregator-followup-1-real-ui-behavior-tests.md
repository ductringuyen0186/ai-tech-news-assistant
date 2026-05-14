# [Bug] Real UI behaviour bugs my contract-only E2E missed; replace with Playwright video-recorded suite

| Field           | Value                                                |
|-----------------|------------------------------------------------------|
| Type            | Bug + Test                                           |
| Priority        | P0                                                   |
| Estimate        | M                                                    |
| Labels          | data-quality, frontend, testing, playwright          |
| Linked design   | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |
| Linked PRD      | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) |
| Linked mission  | [docs/missions/finish-aggregator.md](../missions/finish-aggregator.md) |
| Parent issues   | All 6 milestone issues; this captures gaps the mission's contract-only E2E missed |

## Context

After the user clicked through the running app post-mission, real bugs
surfaced that 16/16 green tests didn't catch. The E2E runner verified
contracts (HTTP 200, valid response shape) but never verified the user-
visible behaviour. Specific failures observed:

1. **89% of articles in `news.db` are seed data** (71/80) titled "OpenAI
   launches GPT-5..." with `source='seed'` and `summary='seed summary'`.
   The wipe step in M5 was never run on the live DB.
2. **All articles have `categories=NULL`** — IngestionService writes
   `source_id` (FK) but not `articles.categories` (JSON). The Topic
   Filter UI matches against `categories`, so any combo returns "0 articles
   found".
3. **Digest tab still shows hardcoded mock data** ("AI Breakthrough in
   Natural Language Understanding", "Quantum Computing Makes Significant
   Progress"). The `/api/digest/` endpoint exists and works, but
   `App.tsx`'s `fetchDigest` was never rewired — it still returns the
   inline mock object. My E2E checked the endpoint shape, never that the
   frontend consumed it.
4. **Chat "Related articles" section shows duplicate entries** — when
   `/api/rag/query` returns multiple mentions of the same article, the
   handler doesn't dedup before rendering.
5. **Chat answer text overflows the chat box container** — long Ollama
   responses break out of the message bubble's CSS bounds. Likely missing
   `max-width` + `overflow-wrap: anywhere` on the bubble and
   `max-height` + `overflow-y: auto` on the panel.
6. **"0 Articles Today" counter** in the header — frontend reads
   `recent_articles` from `/api/news/stats`. Real data shows 80 articles
   in the last 24h, so the value is there; the frontend mapping is wrong
   OR the field is never read and 0 is always shown.

## Description

Three sequential fix workers, then a Playwright UI test suite that records
video so future regressions show up VISUALLY, not just as failed assertions.

### Today
- E2E runner is contract-shape only (HTTP 200, valid JSON shape)
- 71 of 80 DB rows are fake seed data
- Topic filter cannot match anything (categories all null)
- Digest tab is mocked
- Chat is functionally broken (duplicates + overflow)

### After this change
- DB has only real RSS articles, all with categories populated
- Digest tab pulls from `/api/digest/`
- Chat dedups + scrolls properly
- Playwright UI test suite exercises EVERY tab through the actual UI,
  records video, asserts real-data presence
- The skill's runner gets a `--include-ui` flag that runs Playwright as
  the deepest layer of the existing test-app-e2e

## Acceptance criteria

### Worker 1 — data layer
- [ ] `SELECT COUNT(*) FROM articles WHERE source='seed'` returns 0
- [ ] `IngestionService._process_entry` writes the feed's category to
      `articles.categories` (JSON list, e.g. `["AI/ML"]` matching frontend
      filter chips)
- [ ] Re-ingest from RSS produces 50+ real articles, each with
      `categories IS NOT NULL`
- [ ] Frontend filter taxonomy ("AI/ML", "Robotics", "Cloud", "Security",
      etc.) maps to the `category` field on feed configs (update
      `DEFAULT_FEEDS` if needed; AT MINIMUM `Hacker News -> "AI/ML"`,
      `TechCrunch -> "Cloud"` or similar non-empty mapping that lets the
      filter UI actually filter)

### Worker 2 — frontend wiring
- [ ] `App.tsx`'s `fetchDigest` calls `apiFetch(API_ENDPOINTS.digest)` and
      maps the backend response to `digest` state (instead of the inline
      mock)
- [ ] `App.tsx`'s `handleAskQuestion` dedups `sources` by `id` before
      returning `relevantArticles`
- [ ] `ChatInterface.tsx` message bubble has `max-width`,
      `overflow-wrap: anywhere` (or `word-break: break-word`); the panel
      itself has `max-height` + `overflow-y: auto` so long answers scroll
- [ ] `App.tsx`'s "Articles Today" / `recent_articles` counter displays
      the real value from `/api/news/stats` (not 0)

### Worker 3 — Playwright UI tests
- [ ] `frontend/e2e/` directory with `@playwright/test` installed as a
      devDependency
- [ ] `playwright.config.ts` configured with `video: 'on'`,
      `headless: false`, `screenshot: 'only-on-failure'`
- [ ] One test file per tab (or one test per tab in a single spec):
      `news-feed.spec.ts`, `research.spec.ts`, `chat.spec.ts`,
      `digest.spec.ts`, `knowledge-graph.spec.ts`, `settings.spec.ts`
- [ ] Each test asserts user-visible behaviour, not just HTTP. Examples:
      - News Feed: page loads, articles render with non-"seed" titles,
        filter chips actually filter, search returns results
      - Digest: top stories shown have real titles (not hardcoded mock
        strings like "AI Breakthrough in Natural Language Understanding")
      - Chat: type a question, wait for answer, assert the answer is non-
        empty AND fits within the chat box (no overflow), assert
        Related articles list has no duplicates by title
      - Knowledge Graph: nodes render, count >= some minimum, no
        hardcoded "OpenAI ↔ Anthropic ↔ Google" edges from the mock
      - Settings: toggle a category, save, reload page, assert the toggle
        persisted
      - Research: enter query, assert results render
- [ ] `npx playwright test` produces an MP4 video per test under
      `test-results/`
- [ ] A single combined run can be invoked via `npm run test:e2e:ui`
      (script added to `frontend/package.json`)
- [ ] The global `~/.claude/skills/test-app-e2e/SKILL.md` gets a
      reference appended to "behavior testing via Playwright" so future
      missions reach for this pattern

## Out of scope
- Visual regression testing (screenshot diffs)
- Cross-browser testing (Chromium-only is fine for v1)
- Mobile viewport testing (desktop-only matches the original non-goals)
- Re-running every Playwright test on every push (CI hook is a follow-up)

## Verification
Each worker must run their own verification per the worker briefing
template. The orchestrator runs the Playwright suite at the end and
shares the video output path with the user.

## Why this matters as a lesson encoded into the skill

The mission's E2E runner was checking the wrong thing — interface contracts
instead of user behaviour. Future missions on UI projects should default to
Playwright tests, not curl tests. The global `test-app-e2e/SKILL.md` should
say: "for projects with a frontend, generate Playwright tests as the
default behavior layer; the curl tests are a fast smoke layer beneath".
