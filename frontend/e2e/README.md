# Playwright UI behavior tests

This suite exercises the TechPulse AI frontend through the actual browser,
records video for every test, and asserts user-visible behavior — not just
HTTP contracts.

It complements the fast curl-based smoke layer in
`.claude/skills/test-app-e2e/scripts/run_e2e.py`. That one catches contract
breaks (bad JSON shape, 500s); this one catches the bugs the user reported
after clicking through the running app:

- Seed-data leaking onto the news feed
- Digest tab still showing the hardcoded mock strings
- Chat answer text overflowing its bubble
- Duplicate "Related articles" entries in chat
- Settings preferences not persisting across reload

## Prerequisites

The suite assumes the dev stack is already running:

| Service | URL |
| --- | --- |
| Frontend (Vite dev server) | http://localhost:3000 |
| Backend (FastAPI) | http://127.0.0.1:8000 |
| Ollama | http://localhost:11434 |

Start them yourself before running the suite (the suite does NOT spin up
its own webServer — that keeps test runs short and avoids fighting with
the long-running dev workflow).

## Running

From `frontend/`:

```bash
# Install Playwright browsers (one-time, ~120MB)
npx playwright install chromium

# Run all UI tests
npm run test:e2e:ui

# Same thing, but force the browser visible (default config is already
# headed; this is a backup).
npm run test:e2e:ui:headed

# Run a single spec
npx playwright test e2e/news-feed.spec.ts

# Open the last HTML report
npx playwright show-report
```

## Where the videos land

Every test produces a video under:

```
frontend/test-results/<spec-name>/<test-name>/video.webm
```

If a test fails, you also get:

- a screenshot at the failure point
- a full Playwright trace (open with `npx playwright show-trace path/to/trace.zip`)

The HTML report lives at `frontend/playwright-report/index.html`.

## Debugging a failure

1. Watch the video — `frontend/test-results/.../video.webm`. The video is
   the source of truth; the assertion that failed only tells you what
   tripped. Eyeball what actually rendered.
2. Open the trace if available:
   `npx playwright show-trace frontend/test-results/.../trace.zip`
   You get a frame-by-frame timeline of clicks, network requests, DOM
   snapshots — everything you need to localize a regression.
3. Re-run the single spec in headed/UI mode:
   `npx playwright test e2e/<spec>.spec.ts --debug`

## Test design rules

- **Selectors**: prefer `getByRole` / `getByText` / `getByPlaceholder`.
  These survive small CSS refactors. We use class-prefix locators only
  where Radix or Tailwind utility classes are the most stable hook.
- **No mocking**: the whole point is to hit the real backend. If a backend
  call is slow (Ollama, RAG), bump `test.setTimeout`.
- **Video on, screenshot on failure**: configured in
  `playwright.config.ts`. Every run leaves a video trail behind.
- **If the UI is genuinely broken**: do NOT silently change the test to
  pass. Document the failure in the worker handoff. The point of this
  layer is to surface real bugs.

## Adding a new tab spec

Use one of the existing files as a template. Each spec should:

1. `page.goto("/")` and assert the header is visible.
2. Click the relevant tab.
3. Wait for that tab's content (NOT just a network idle — content-driven).
4. Assert what the user actually sees, not just an HTTP shape.
5. Where applicable, prove persistence by reloading and re-checking.
