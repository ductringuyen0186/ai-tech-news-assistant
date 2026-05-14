# Mission: Daily News Ingestion

> **Executive summary.** Ship a daily-at-05:00-UTC cron job that fetches new articles from the RSS sources, summarises them with Ollama (or cloud LLM in prod), embeds them with sentence-transformers, runs entity extraction, and writes everything atomically. Reuses the existing `APScheduler` instance already running daily retention. Five small milestones, ~6-10 hours of work. Adds zero new infrastructure; in production the same job runs on Render Cron or GitHub Actions on a schedule.

## 0. Why this matters

Right now the corpus is **frozen**. The `articles` table has 80 rows, most dated 2026-05-07 — a week stale. The Welcome page wire, News Feed, Digest, Knowledge Graph, and (most importantly) Agentic Research all read from this table. Without daily ingestion the product visibly rots: "Recent news" stops being recent, the wire stops feeling alive, the agent stops finding articles for current questions.

The plumbing is mostly already there:

- `backend/src/services/ingestion_service.py` — fetches + parses RSS feeds.
- `backend/src/services/summarization_service.py` — Ollama-backed article summarization.
- `backend/src/services/embedding_service.py` + `vectorstore/embeddings.py` — 384-dim sentence-transformer embeddings.
- `backend/src/services/entity_extraction_service.py` — pulls companies/people/products from article bodies.
- `backend/src/main.py:120` — `APScheduler` is **already running**, currently only firing daily retention at 00:00 UTC.
- `backend/scripts/backfill_embeddings.py` — proven backfill script (just used to fix the M2.M4 RAG bug).

What's missing: a single orchestration function that chains those services together, wired into the scheduler, with retry semantics and observability.

## 1. Resolved decisions

1. **Use APScheduler in-process for dev, External cron in prod.** The same orchestration function gets called from both. APScheduler keeps the dev loop fast; production swaps to Render Cron or GitHub Actions Schedule so the web service can scale to zero between runs.
2. **Schedule: 05:00 UTC daily.** That's ~01:00 ET / 22:00 PT — past the US east-coast publishing rush, before the European morning skim.
3. **Idempotent.** Articles are deduplicated by URL hash; re-running on the same day adds zero rows.
4. **Per-article failure isolated.** One bad feed parse must not poison the run. Each phase logs its failures and continues.
5. **No backfill of history.** This mission only handles "what's new today." Backfill of the legacy 86KB `articles.db` corpus is a separate concern.

## 2. Mission shape

Five milestones. Each is small enough to land in one session.

### M1 — Orchestrator function (`run_daily_ingestion()`)

**Goal.** A single async function that runs the full pipeline.

**Files touched.**
- `backend/src/services/daily_ingestion_orchestrator.py` (new, ~250 lines)
- `backend/tests/unit/test_daily_ingestion_orchestrator.py` (new)

**Shape.**

```python
async def run_daily_ingestion(
    db_path: str,
    *,
    feeds: list[str] | None = None,
    summarize: bool = True,
    embed: bool = True,
    extract_entities: bool = True,
    dry_run: bool = False,
) -> DailyIngestionReport:
    """Fetch -> dedupe -> summarize -> embed -> entity-extract.

    Returns a structured report (counts per phase, durations, failures).
    Each phase is wrapped in try/except so one failure doesn't kill the run.
    """
```

**Phases (in order, all observable):**

1. **Fetch.** Call `IngestionService.fetch_all_feeds()`. Drop articles whose URL hash already exists in `articles`. Insert remaining rows with `published_at`, `content`, `source`. Log `[fetch] new=X duplicates=Y errors=Z`.

2. **Summarize.** For every article where `summary IS NULL`, call `SummarizationService.summarize(content)`. Write back. Log `[summarize] processed=X failed=Y avg_ms=Z`.

3. **Embed.** For every article where `id NOT IN (SELECT article_id FROM article_embeddings)`, generate a 384-dim vector and insert. This is the exact logic in `scripts/backfill_embeddings.py` — extract the loop into a callable helper and call from both places. Log `[embed] new_embeddings=X failed=Y`.

4. **Entity-extract.** For every article without an `entity_mentions` row, run `EntityExtractionService` and write the company/person/product mentions. Log `[entities] new_mentions=X entities_created=Y`.

5. **Report.** Build a `DailyIngestionReport` Pydantic model with per-phase counts + durations + first 5 error strings per phase. Log as a single JSON line so it's grep-able.

**Test risk.** This wraps existing services, all of which have unit tests. The new test just mocks each service and asserts the orchestrator (a) calls them in order, (b) survives a mid-pipeline exception in one phase, (c) returns a `DailyIngestionReport` with the right shape.

### M2 — Wire into APScheduler

**Goal.** Schedule M1's function to fire at 05:00 UTC daily, alongside the existing retention job.

**Files touched.**
- `backend/src/main.py` (the `lifespan` startup section that already adds the retention scheduler — add a second `scheduler.add_job` call).

**Shape.**

```python
scheduler.add_job(
    run_daily_ingestion,
    CronTrigger(hour=5, minute=0, timezone="UTC"),
    id="daily_ingestion",
    name="Daily article ingestion",
    kwargs={"db_path": settings.database_path},
    misfire_grace_time=3600,        # if missed, run within 1 hour
    coalesce=True,                  # collapse missed runs into one
    max_instances=1,                # never run two simultaneously
)
```

Also add a one-shot "startup ingestion run" 60 seconds after boot (only when an env var `RUN_INGESTION_ON_BOOT=1` is set — useful for dev, off in prod).

**Test risk.** Zero. The retention scheduler already proves APScheduler integration works; this is a second job in the same pattern.

### M3 — Manual trigger endpoint (admin-only)

**Goal.** Add `POST /api/admin/ingest` that runs M1's orchestrator on demand. Lets you re-run after a feed outage without waiting 24 hours, and exposes the report as JSON for the frontend (optional dashboard later).

**Files touched.**
- `backend/src/api/routes/admin.py` (new, ~80 lines)
- `backend/src/main.py` (router include)

**Shape.**

```python
@router.post("/ingest", response_model=DailyIngestionReport)
async def trigger_ingestion(
    request: Request,
    admin: bool = Depends(require_admin),  # X-Admin-Token header check
    dry_run: bool = Query(False),
) -> DailyIngestionReport:
    return await run_daily_ingestion(settings.database_path, dry_run=dry_run)
```

Auth: stupid-simple HMAC of a shared secret in `ADMIN_TOKEN` env var. No user table required (we have zero users). Just `X-Admin-Token: <env>` header check.

**Test risk.** New endpoint; tests cover happy path (returns report) and 401 on missing/wrong token.

### M4 — Observability + alerts

**Goal.** Catch ingestion failures before the user notices stale data.

**Files touched.**
- `backend/src/services/daily_ingestion_orchestrator.py` (extend the report with a `health_status` field — `green`/`yellow`/`red`)
- `backend/src/main.py` (add a `GET /api/health/ingestion` endpoint that returns the last report)

**Shape.**

- `health_status` = `green` when phase 1 (fetch) returns ≥ 1 new article AND no phase had > 50% failures.
- `health_status` = `yellow` when 0 new articles fetched (feeds may be quiet today, not necessarily broken) OR 1 phase had errors.
- `health_status` = `red` when 2+ phases failed OR the entire run threw.
- Persist the latest report to a `ingestion_runs` table for trend visibility.
- Optional: when status flips `green` → `red`, fire a webhook to `INGESTION_ALERT_WEBHOOK` env var (Slack, Discord, Telegram bot — same shape, JSON POST).

**Test risk.** None for the data model. The webhook send is best-effort; failures log a warning and don't fail the job.

### M5 — Production scheduler swap

**Goal.** When deploying to production, replace the APScheduler in-process job with an external cron so the web service can scale to zero and the cron runs even if the web service is sleeping.

**Files touched.**
- `.github/workflows/daily-ingestion.yml` (new, GitHub Actions schedule trigger)
- `docs/deployment/production-plan.md` (cross-link)

**Shape.**

```yaml
on:
  schedule:
    - cron: "0 5 * * *"  # 05:00 UTC daily
  workflow_dispatch: {}    # manual trigger via GitHub UI

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -fsS -X POST \
            -H "X-Admin-Token: ${{ secrets.ADMIN_TOKEN }}" \
            https://api.techpulse.example.com/api/admin/ingest
```

GitHub Actions cron is free for public repos and 2000 min/month for private — way under our needs. Render Cron Jobs ($1/month) is the alternative if we don't want to depend on GitHub.

**Test risk.** Workflow runs in CI, hits live prod. Add a `--dry-run` flag for the first invocation to smoke-test without writing rows.

## 3. Timeline + scope

| Milestone | Effort | Blocking? |
| --- | --- | --- |
| M1 — Orchestrator function | 3-4 hrs | yes |
| M2 — APScheduler wire-up | 30 min | depends on M1 |
| M3 — Admin endpoint | 1 hr | depends on M1 |
| M4 — Observability | 1-2 hrs | nice-to-have |
| M5 — Production cron | 30 min | only at deploy time |

**Total: 6-8 hours** of focused work. M1 is the only milestone with real code surface. M2-M5 are config + glue.

## 4. Open questions

1. **Feed list.** Currently `IngestionService` pulls TechCrunch, The Verge, Wired, Ars Technica, MIT Tech Review, Hacker News. Want to expand? (Bloomberg Tech, FT Tech, Stratechery, The Information — these are paywalled feeds; full-text fetch needs cookies or RSS-only summaries.)
2. **LLM choice for summarization.** Local Ollama (gpt-oss:20b) is fine in dev but slow and Mac-only in prod. The summarization runs once per article; if we ingest ~30 articles/day, that's ~30 calls/day. Groq llama-3.1-8b-instant is free up to 14400 req/day — overkill cheap. Worth the swap when we go to prod (see deployment plan).
3. **Retention vs growth.** The existing retention job deletes anything older than 30 days. If we ingest ~30/day, steady state is ~900 articles. Acceptable, but want to consider archiving (delete to a `articles_archive` table instead of dropping) if we want historical research.
4. **First-run cost.** When the daily job first runs on a new install it'll try to summarize + embed any backlog. With 80 existing articles already done, this is zero. On a fresh database (e.g. someone clones the repo), the orchestrator should run the existing backfill scripts as a one-shot. Already handled by the updated `start-dev.ps1` preflight.

## 5. Deliverable

A single new file `backend/src/services/daily_ingestion_orchestrator.py`, two new endpoints, one APScheduler job, one GitHub Actions workflow, one new admin token env var. Build green, tests green, manual hit of `POST /api/admin/ingest` returns a `DailyIngestionReport` with `health_status=green` and N new articles in the DB.
