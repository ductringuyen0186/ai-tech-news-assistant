# Mission: Finish AI Tech News Aggregator

| Field             | Value                                                          |
|-------------------|----------------------------------------------------------------|
| Status            | **SHIPPED ✅** — All 6 milestones complete                     |
| Started           | 2026-05-07                                                     |
| Completed         | 2026-05-07 (single-day execution, well ahead of May-17 target) |
| Design context    | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |
| PRD               | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) |
| Approval          | "start handing milestones to workers" — 2026-05-07             |
| Final E2E         | **16/16 PASS** on Windows + real Ollama                        |
| Total commits     | 10 (6 features + 4 fix-ups)                                    |

## Mission constraints (set at Phase 2)

- Retry budget: 3 worker retries per milestone, then escalate
- Cadence: autonomous mode — orchestrator escalates only when stuck
- Concurrency: workers serial, validators parallel within a milestone
- Stop conditions: validator fails 3× / user pause / Ollama unreachable

## Final commit chain

```
27d7cbc feat: knowledge-graph entity extraction (M6)
32ce60a fix: don't pass source name string to Article ORM (M5 follow-up)
0d849f7 feat: clean re-ingest reset script + admin wipe + live ingest smoke (M5)
ad97c65 fix: align backend Docker build with Python 3.13 (M4 follow-up)
02b1145 feat: VPS deploy infrastructure (M4)
30f5985 fix: address M3 retention scrutiny findings (M3 retry)
7fa0971 feat: add daily retention cron with admin route (M3)
24035b0 fix: restore truncated App.tsx footer (M2 retry)
e0b065b feat: persist user settings server-side via /api/settings (M2)
7438761 chore: clean up stale tests and dead code in news_service (M1)
```

## Milestone outcomes

| # | Milestone | Estimate | Result | Commit(s) | Validators |
|---|-----------|----------|--------|-----------|------------|
| 1 | Cleanup + dead-code pass | S | ✅ Done | `7438761` | Scrutiny PASS |
| 2 | Settings persistence | M | ✅ Done (1 retry) | `e0b065b` + `24035b0` | Scrutiny FAIL→PASS, User-testing PASS |
| 3 | Retention cron | S | ✅ Done (1 retry) | `7fa0971` + `30f5985` | Scrutiny FAIL→PASS |
| 4 | Deploy infrastructure | L | ✅ Done (+ build follow-up) | `02b1145` + `ad97c65` | Scrutiny PASS + mandatory follow-up |
| 5 | Clean re-ingest in prod | S | ✅ Done (+ ingest follow-up) | `0d849f7` + `32ce60a` | Scrutiny PASS + mandatory follow-up |
| 6 | Knowledge Graph entity extraction | L | ✅ Done | `27d7cbc` | Scrutiny PASS (with OneDrive corruption note) |

## What the user has now

### Backend
- 14 routes registered including new `/api/settings/`, `/api/admin/wipe`,
  `/api/admin/retention/run`, `/api/knowledge-graph/`
- APScheduler-driven daily retention with proper test-environment gating
- Real entity extraction via Ollama with sanity rules + acronym whitelist
- Idempotent entity persistence (`(article_id, entity_id)` uniqueness)
- Docker image builds cleanly on Python 3.13
- Fixed long-standing `'str' object has no attribute '_sa_instance_state'`
  ingestion bug

### Frontend
- All 6 tabs (News, Research, Chat, Digest, Knowledge Graph, Settings)
  driven by real backend data — no mocks remaining anywhere
- Settings persisted via `GET/PUT /api/settings/`; localStorage demoted
  to offline cache
- Knowledge Graph populated by live entity extraction with proper canvas
  rendering, zoom, type-coloured nodes, edge weighting

### DevOps
- `docker-compose.prod.yml` — backend + ollama on 127.0.0.1, named
  volumes, memory limits, project-namespaced for VPS co-tenancy
- `deployment/Caddyfile.example` — auto-TLS, hardening headers, gzip
- `.github/workflows/deploy.yml` — push-to-main → test → build → push
  GHCR → SSH → `docker compose pull && up -d` → live E2E gate
- `docs/runbooks/first-deploy.md` — end-to-end VPS provisioning guide
- `scripts/reset_data.sh` — wipe + re-ingest with `--prod` confirmation
- `docs/runbooks/reset-prod-data.md`

### Testing
- 16/16 E2E suite covering every tab + every endpoint
- 3 validators-bundled tests added during the mission:
  `settings_persistence`, `retention_dry_run`, `kg_endpoint`, `kg_no_mock`
- Plus opt-in `live_ingest_smoke` (gated behind `--include-live-ingest`)

## Live verification (final, on user's Windows + real Ollama)

```
[PASS] (critical) infra      backend_reachable             24ms
[PASS] (high    ) api        health_payload                27ms
[PASS] (high    ) api        news_list_endpoint            19ms
[PASS] (medium  ) api        news_stats_endpoint           28ms
[PASS] (medium  ) api        summarize_status_endpoint    503ms
[PASS] (medium  ) api        ingest_status_endpoint         2ms
[PASS] (medium  ) config     cors_for_frontend              5ms
[PASS] (high    ) infra      ollama_reachable               2ms
[PASS] (medium  ) feature    news_sources_endpoint          5ms
[PASS] (medium  ) feature    digest_endpoint                4ms
[PASS] (high    ) feature    semantic_search_endpoint    1530ms
[PASS] (high    ) feature    chat_rag_endpoint           4417ms
[PASS] (medium  ) feature    settings_persistence         150ms
[PASS] (high    ) feature    retention_dry_run             28ms
[PASS] (high    ) feature    kg_endpoint                   26ms
[PASS] (medium  ) config     kg_no_mock                    10ms
```

Live `/api/knowledge-graph` sample output (post-ingestion of seed
articles, real Ollama):
- 13 entities extracted (Anthropic, Claude, GPT-4, Microsoft, AWS,
  Google Cloud, OpenAI, ...)
- 5 co-mention edges with weights
- Junk correctly rejected (AI, NEWS, TODAY, generic words)
- Real acronyms preserved (AWS, GPT-5)

## Out of scope (deferred — not blocking)

- VPS provisioning (user picks provider + walks through `first-deploy.md`)
- Domain registration (Caddy works on raw IP first)
- The first live deploy (workflow ready; one-button after VPS is up)
- Real auth / multi-user (explicit non-goal)
- Mobile-responsive design (explicit non-goal)
- Postgres migration (explicit non-goal)

## Top mission-level lessons (encoded for future runs)

1. **OneDrive truncation can hit AFTER commit lands.** The git commit is
   internally consistent but on-disk files get silently truncated
   minutes later by sync. `git checkout HEAD -- <file>` is the recovery.
   Future workers MUST verify post-write integrity. Future
   orchestrators should snapshot the working tree against `git show
   HEAD --` before declaring milestones complete.

2. **Python 3.11+ StrEnum semantics changed**: `str(MyEnum.X)` now
   returns `"MyEnum.X"`, not `"x"`. Always compare enum identity (`==`)
   or `.value`. (Surfaced in M3 — would have shipped a broken gate
   without empirical validator testing.)

3. **Pre-existing bugs become blockers when CI starts running them.**
   M4 surfaced a Dockerfile/numpy mismatch; M5 surfaced an SQLAlchemy
   relationship-vs-string bug. Both fixed via tightly-scoped follow-up
   workers, not by reopening the milestone. The pattern: scrutiny
   validator finds it → orchestrator decides "include in milestone" or
   "follow-up issue" based on whether downstream milestones depend on
   the fix.

4. **Adversarial validators catch what user-testing validators miss.**
   In M2, the user-testing validator passed (curl round-trip worked) but
   scrutiny caught the truncated React file (vite build would fail).
   Run both in parallel when there's UI involved.

5. **"Empirical gate test"** — for any new conditional that gates a
   background job, validators must boot the app with the gate active
   AND inactive, and check the log line. Don't trust `if` statements
   visually. Encoded into validator briefings going forward.

6. **Workers should never use `--break-system-packages` or
   `continue-on-error: true` to mask real problems.** Both M4 workers
   refused these escape hatches and surfaced the real issues for
   follow-up. This discipline is worth defending hard.
