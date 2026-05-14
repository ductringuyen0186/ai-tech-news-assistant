# PRD: Finish AI Tech News Aggregator (portfolio polish + VPS deploy)

| Field          | Value                                                          |
|----------------|----------------------------------------------------------------|
| Status         | Draft                                                          |
| Author         | duc                                                            |
| Owner          | duc (eng + product, single-maintainer)                         |
| Stakeholders   | — (single-user portfolio piece)                                |
| Created        | 2026-05-07                                                     |
| Last updated   | 2026-05-07                                                     |
| Target ship    | 2026-05-17 (Sun, end of next week — 10 days)                   |
| Design context | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Summary

Bring the AI Tech News Aggregator from "shell with mocked tabs" to "every UI
tab works on real data, deployed to a multi-project VPS via push-to-main
CI/CD, with daily retention." Audience is backend / infra / platform
recruiters who will both click the live URL and read the codebase. The skill
suite that orchestrates this build (`grill-me`, `write-prd`, `write-issue`,
`missions`, `test-app-e2e`) is itself part of the portfolio narrative.

## Problem

Today, four of the six UI tabs are visibly weak:
- **Knowledge Graph** is hardcoded mock data; recruiter clicks it, sees fake
  "OpenAI ↔ Anthropic" edges, immediately knows it's a stub.
- **Settings filter** persists only to localStorage; preferences vanish on a
  fresh browser. Subtle but unprofessional.
- **Chat / Research** work but quality is bounded by the local 1B model.
- The whole project runs only on `localhost`, so there's no live URL to
  share. A portfolio piece without a clickable demo loses 80% of its impact.

Backend-audience reviewers also won't be impressed by a repo with stale
imports, a broken legacy test directory, and no deploy story. Code quality
and architecture are part of the product for this audience.

## Goals & non-goals

### Goals
- Every UI tab driven by real backend data (no hardcoded mocks anywhere)
- Settings persisted server-side, not just in localStorage
- Knowledge Graph populated by real entity extraction from article text
- Daily retention job keeps the DB bounded (`published_at < now() - 30d`)
- Deployed to a VPS at a live subdomain, behind Caddy, alongside other
  portfolio projects
- Push to `main` → GitHub Actions → SSH → `docker compose pull && up -d`
  produces an updated live site within ~5 minutes
- The 13-test E2E suite stays green; new tests added for the new endpoints
- The codebase reads cleanly to a backend reviewer (no dead code, no
  orphan tests, no commented blocks)

### Non-goals
- Real auth / multi-user / login (single-user only)
- Mobile-responsive design (desktop browser only)
- Migrating off SQLite to Postgres
- Hosted LLM providers (Groq / OpenAI / Anthropic) — Ollama on VPS only
- Real-time push / websockets
- Uptime monitoring / alerting beyond GitHub Actions notifications
- Replacing existing skills — extend, don't refactor

## Users & use cases

### Primary user
The maintainer (single-user portfolio piece). Reads news daily, occasionally
points recruiters at the live URL.

### Secondary user
Backend / infra / platform engineering recruiters and hiring managers who:
1. Click the live URL, look around, and form a quick impression
2. Read the GitHub repo, evaluate code quality and architecture choices

### Use cases
1. **Daily catch-up**. Maintainer opens the live URL at breakfast, scans 5–8
   AI-summarised stories from the last 24h, taps Knowledge Graph to see
   real entity relationships from this week's news.
2. **Recruiter click-through**. Recruiter receives the URL, lands on the
   page, clicks every tab in 90 seconds. Each tab shows real, current
   content. They mentally check "the demo works".
3. **Recruiter code-read**. Same recruiter clicks through to GitHub. The
   repo has a clean structure, runnable locally with one command, idiomatic
   FastAPI + SQLAlchemy + React. CI is green; deploy pipeline is visible
   in `.github/workflows/`.

## Requirements

### Functional
- `PUT /api/settings` writes a settings JSON to the DB, returns the saved
  shape; `GET /api/settings` returns it. Frontend `App.tsx` calls both
  instead of touching localStorage as truth.
- New entity-extraction service runs on each article post-summarisation,
  identifies named entities (companies, people, products, technologies),
  persists to `entities` + `entity_mentions` tables.
- `GET /api/knowledge-graph` returns top-N entities (by mention count) plus
  edges (entities co-mentioned in same article). Frontend `KnowledgeGraph.tsx`
  calls this; mock data is removed.
- Retention service runs daily (APScheduler, midnight UTC), hard-deletes
  articles where `published_at < now() - RETENTION_DAYS` (default 30); FK
  cascades clean up summaries / embeddings / entity-mentions.
- VPS-resident `docker-compose.yml` runs backend (FastAPI), Ollama,
  retention cron — all behind a single shared Caddy reverse proxy on the
  host that routes `news.<domain>` to backend port via `127.0.0.1`.
- GitHub Actions on `main` builds image, pushes to GHCR, SSHes into VPS,
  runs `docker compose pull && docker compose up -d`. Existing `news.db`
  volume survives.
- Stale tests under `backend/tests/` that import the deleted `utils`
  package are deleted. Pytest collection completes without errors.

### Non-functional
- **Performance**: `/api/knowledge-graph` responds in p95 < 500 ms on the
  VPS for top-50 entities. Retention job completes in < 30s for 1000-row DB.
- **Reliability**: Live site uptime ≥ 99% measured by manual probe over the
  first month. Failed deploys do not take down sibling projects on the VPS.
- **Security**: All `.env` secrets live in `/etc/news/.env` on the VPS,
  mode 0640, never echoed in CI logs. GitHub Secrets store only the deploy
  SSH key + GHCR pull token. CORS restricted to the public subdomain only.
- **Compute**: Ollama (`llama3.2:1b`) runs on the same VPS with
  `OLLAMA_KEEP_ALIVE=5m` so it doesn't squat memory full-time. Per-container
  memory limits in compose: backend 512 MB, Ollama 2 GB, retention 128 MB.
- **Code quality**: every new module has a one-paragraph docstring; every
  new endpoint has a Pydantic response model; every new DB table has at
  least one unit test plus an entry in the E2E suite.

## Success metrics

### Leading indicators (week 1 after deploy)
- All 16+ E2E tests pass (13 existing + 3 new) on each push to `main`
- Daily retention job runs and logs successful deletions for 7 consecutive
  days
- Push-to-main → live within 5 minutes for at least 3 consecutive deploys

### Lagging indicators (30 days)
- Article count stays bounded (oscillates around the steady-state of
  ~daily-ingest × 30 ≈ 600–2000 rows depending on feed activity)
- VPS RAM usage stays under 80% of capacity even with Ollama loaded
- No 5xx incidents lasting > 5 minutes recorded in deploy logs

### Rollback criteria (auto-trigger or maintainer-trigger)
- Live site returns 5xx for > 5 consecutive minutes
- Ollama OOMs and crashes the VPS host
- Any E2E test goes red against the live URL post-deploy
  (test-app-e2e runs against the live URL as part of post-deploy CI)

## Rollout plan

**Strategy: straight to live URL once deployable.** No staging period; the
deploy pipeline becomes the gate. Each milestone after milestone 4 ships
to prod as it lands.

1. **Days 1–2 (May 7–8)** — Milestones 1 + 2: stale-test cleanup, settings
   persistence. All on localhost; no deploy yet.
2. **Day 3 (May 9)** — Milestone 3: retention cron. Still localhost.
3. **Days 4–6 (May 10–12)** — Milestone 4: deploy infrastructure (Caddy +
   Compose + GitHub Actions). First successful push-to-main → live deploy
   marks the cutover.
4. **Day 7 (May 13)** — Milestone 5: wipe + clean re-ingest in production.
   Validates the deploy + retention + ingest loop end-to-end.
5. **Days 8–10 (May 14–17)** — Milestone 6: Knowledge Graph entity
   extraction. Heaviest ML lift; ships incrementally to live.
6. **Day 10 (May 17, end of day)** — Final mission report; if all
   validators green, mark v1 shipped.

## Milestones & validation contracts

The Missions orchestrator will spawn one worker subagent per milestone. Each
worker gets the milestone's validation contract; each scrutiny + user-testing
validator runs that contract independently against the worker's git diff.

### Milestone 1 — Cleanup + dead-code pass *(S, ~0.5 day)*

**Goal.** Repo reads cleanly. Stale test files gone, leftover dead code
removed, pytest collection green.

**Validation contract:**
- `pytest backend/tests/ --collect-only` exits 0 (no import errors)
- `grep -rn "from utils\." backend/src` returns empty
- No commented-out function definitions left in `backend/src/`
- The 13 E2E tests still pass

### Milestone 2 — Settings persistence *(M, ~1 day)*

**Goal.** Settings round-trip through the backend; localStorage is
optimisation, not truth.

**Validation contract:**
- `GET /api/settings` returns `{success, data: {categories: [...], view_mode, ...}}` with HTTP 200
- `PUT /api/settings` with a valid body persists and returns the saved
  shape; subsequent `GET` returns the new value
- New `Settings` table has migration applied on app start; one row max
  (single-user)
- Frontend `App.tsx` `useEffect` on mount calls `GET /api/settings`,
  populates state. `TopicFilter.onSave` calls `PUT /api/settings`.
- New E2E test `settings_persistence` PUTs a value, GETs it back, asserts
  equality
- Refresh-the-browser test: maintainer changes a category, refreshes, sees
  the change persisted (manual check)

### Milestone 3 — Retention cron *(S, ~0.5 day)*

**Goal.** DB stays bounded. Articles older than 30 days disappear daily.

**Validation contract:**
- `RETENTION_DAYS` env var defaults to 30; overrideable
- Service runs at startup + once daily via APScheduler
- Dry-run mode logs deletion IDs without committing
- New E2E test `retention_dry_run` posts an article with
  `published_at = now() - 31 days`, runs the retention job, asserts the
  article is gone (or marked for deletion in dry-run)
- Cascades remove summaries / embeddings / entity-mentions for deleted
  articles (FK ON DELETE CASCADE)
- Per-run deletion cap (`RETENTION_MAX_DELETES=500`) prevents runaway

### Milestone 4 — Deploy infrastructure *(L, ~3 days)*

**Goal.** A push to `main` lands on a live subdomain in under 5 minutes,
self-contained, doesn't disturb sibling projects.

**Validation contract:**
- `docker-compose.yml` (production variant) brings up backend + Ollama +
  retention container; backend on `127.0.0.1:<port>` only (not exposed)
- Caddyfile routes `news.<domain>.tld` → backend; auto-issues TLS via
  Let's Encrypt
- GitHub Actions workflow `.github/workflows/deploy.yml`:
  - Triggers on push to `main`
  - Runs the existing CI tests; deploy fails if tests fail
  - Builds + pushes Docker image to GHCR with `:main` and `:<sha>` tags
  - SSHes into VPS using a deploy key stored in GitHub Secrets
  - Runs `docker compose pull && docker compose up -d`
  - Posts a status comment on the commit
- Deploy completes in under 5 minutes for a no-op change
- Sibling project containers on the VPS continue running across the deploy
- E2E suite runnable against the live URL: `python run_e2e.py --backend
  https://news.<domain>.tld --frontend https://news.<domain>.tld`

### Milestone 5 — Wipe + clean re-ingest in production *(S, ~0.5 day)*

**Goal.** Single command on the VPS produces a fresh, internally-consistent
data state. Validates the live system end-to-end.

**Validation contract:**
- `scripts/reset_data.sh` (or equivalent) wipes `news.db`, runs migrations,
  triggers `POST /api/ingest/`, waits for completion
- After running, `GET /api/news/stats` returns `total_articles >= 50`
  (sanity bar; depends on RSS feed health)
- All articles have non-null summaries (orchestrator ran)
- `articles_with_embeddings` > 0 (indicates the embedding step ran)
- E2E test `live_ingest_smoke` posts a fresh ingest against live URL and
  verifies new articles appear

### Milestone 6 — Knowledge Graph entity extraction *(L, ~3 days)*

**Goal.** Knowledge Graph tab shows real entities and edges extracted from
article text. No hardcoded mock anywhere in the path.

**Validation contract:**
- New `EntityExtractionService` extracts named entities from each article's
  summary + content using Ollama (prompt-based) or sentence-transformers
- New tables `entities` (id, name, type, mention_count) and
  `entity_mentions` (article_id, entity_id, position) populated via the
  service
- Sanity rules reject extracted strings: under 3 chars, all-uppercase
  non-acronym, common stopwords, single English words
- `GET /api/knowledge-graph?limit=50` returns top-N entities (by
  `mention_count`) + edges (pairs co-mentioned in ≥ 2 articles)
- Frontend `KnowledgeGraph.tsx` calls the endpoint, removes the mock
  fallback, renders nodes + edges. Canvas tolerates 50+ nodes (zoom + pan).
- New E2E tests:
  - `kg_endpoint` — returns valid `{nodes, edges}` shape with non-zero
    nodes after fresh ingest
  - `kg_no_mock` — `grep -rn "mockData" frontend/src/components/KnowledgeGraph.tsx`
    returns empty (no static fallback in the production code path)

## Dependencies

- **Internal**: existing `IngestionService` + `SummarizationOrchestrator` +
  `test-app-e2e` skill all stay functional. Milestones 4–6 depend on
  milestones 1–3 being clean first.
- **External**: a VPS provider must be picked before milestone 4 starts.
  The user committed to "pick later" — recommended Hetzner CPX21 / DO 4 GB.
- **Blockers / unblocks**: blocks nothing else in the user's portfolio.
  Unblocks the live URL the user can put on a résumé.

## Risks & mitigations

| Risk                                          | Likelihood | Impact | Mitigation                                                                |
|-----------------------------------------------|------------|--------|---------------------------------------------------------------------------|
| Ollama hallucinates junk entities             | High       | Med    | Sanity rules in service; reject on length / case / stopword               |
| KG canvas chokes on 50+ nodes                 | Med        | Low    | API limits to top-N; frontend adds zoom + filter                          |
| Re-ingest pulls partial RSS state             | Low        | Low    | Tolerate; orchestrator records `sources_processed`; skip retention if < 50% feeds responded |
| VPS RAM exhausted by Ollama + sibling projects| Med        | High   | Per-container memory limits; `OLLAMA_KEEP_ALIVE=5m`; document VPS sizing  |
| Retention job deletes wrong rows              | Low        | High   | Dry-run mode for first prod run; per-run cap; log all deletion IDs        |
| CI/CD secrets leak                            | Low        | High   | Never echo env in logs; least-privilege deploy user; rotate SSH key       |
| Deploy breaks sibling project on VPS          | Low        | High   | Per-project compose project name + network namespace                      |
| 10-day timeline slips                         | Med        | Low    | Milestones are independently shippable; non-goals already trimmed         |
| Domain not chosen by milestone 4              | Low        | Med    | Caddy works on raw IP first; swap subdomain in via DNS + 1-line Caddyfile |

## Open questions

- **Ollama deployment shape on VPS**: sibling Docker service vs. host-installed
  daemon. Trade-offs: container is cleaner but adds 1 GB image; host daemon
  is leaner but couples the project to host config. *Owner: duc, decide
  during milestone 4.*
- **Domain name**: still unselected. Won't block deploy; raw IP works for
  testing. *Owner: duc, decide before sharing the live URL.*
- **Should retention also prune `entities` rows that have zero remaining
  mentions?** Almost certainly yes (orphan rows are noise). *Owner: duc,
  spec in milestone 6 issue.*
- **Per-deploy E2E run against live**: should it block the deploy, or just
  alert? Suggest: block on the first 3 deploys, then alert-only after we
  trust the pipeline. *Owner: duc, decide during milestone 4.*

## Out of scope (FAQ-style)

**Q: Will this also do real-time updates / push notifications?**
A: No. Refresh-on-load is fine for v1. WebSockets / SSE not in scope.

**Q: Will I be able to log in and have my own account?**
A: No. Single-user portfolio piece. No auth.

**Q: Why not deploy to Render or Vercel free tier?**
A: They wipe disk on every deploy, which destroys ingested article data;
they're per-project so don't help with multi-project hosting; they don't
let you run Ollama. A VPS solves all three at once.

**Q: Will the live site work on my phone?**
A: Functionally yes, visually probably not great. Mobile-responsive is an
explicit non-goal for v1.

**Q: Is this going to cost money?**
A: ~$5–10/month for the VPS (Hetzner CPX21 ≈ $8). Domain is optional;
if registered, ~$10/year. Everything else (LLM, RSS, GitHub Actions, GHCR
for public repos, Let's Encrypt) is free.

## Appendix

- **Source design context**: [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md)
- **Skill suite that orchestrates this build**:
  - [.claude/skills/grill-me/](../../.claude/skills/grill-me/SKILL.md) — design context
  - [.claude/skills/write-prd/](../../.claude/skills/write-prd/SKILL.md) — this doc
  - [.claude/skills/write-issue/](../../.claude/skills/write-issue/SKILL.md) — per-milestone tickets
  - [.claude/skills/missions/](../../.claude/skills/missions/SKILL.md) — orchestrated execution
  - [.claude/skills/test-app-e2e/](../../.claude/skills/test-app-e2e/SKILL.md) — validation
- **Existing E2E baseline**: 13 tests passing, 4 covering feature-level
  endpoints (chat, semantic search, digest, news sources)
- **Conversation log**: see design context, sections "Round 1–5"
