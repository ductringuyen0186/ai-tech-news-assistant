# [Feature] Add daily retention cron that deletes articles older than RETENTION_DAYS

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Feature                                              |
| Priority       | P1                                                   |
| Estimate       | S                                                    |
| Assignee       | unassigned                                           |
| Labels         | backend, scheduler, data-lifecycle                   |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 3 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
Once deployed, the DB will accumulate ingested articles indefinitely.
For a portfolio piece on a small VPS, that's both wasteful and stale-y.
The design committed to a daily cron that hard-deletes articles where
`published_at < now() - RETENTION_DAYS`.

## Description
**Today:** No retention. `news.db` grows without bound.

**After this change:** APScheduler-driven service runs daily (00:00 UTC),
hard-deletes old articles, cascades to summaries / embeddings /
entity-mentions via FK ON DELETE CASCADE. Configurable via env var.

## Acceptance criteria
- [ ] `RETENTION_DAYS` env var defaults to 30; readable via settings
- [ ] `RETENTION_MAX_DELETES` env var defaults to 500 (per-run cap)
- [ ] APScheduler job registered in `src/main.py` lifespan; runs on
      startup AND once daily at 00:00 UTC
- [ ] `RetentionService.run(dry_run=False)` deletes rows where
      `published_at < now() - RETENTION_DAYS`, capped at `RETENTION_MAX_DELETES`
- [ ] Dry-run mode (`dry_run=True`) logs what it WOULD delete without
      committing
- [ ] FK cascades remove related rows (summaries / embeddings /
      entity-mentions for deleted articles)
- [ ] Every run logs: total scanned, IDs to be deleted, final count deleted
- [ ] New E2E test `retention_dry_run`: insert article with `published_at = now() - 31d`,
      run service in dry-run, assert it's listed; run live, assert it's gone
- [ ] Service exposes a `POST /api/admin/retention/run?dry_run=true` route
      for manual triggering (useful for the first prod run)

## Implementation notes
Files likely involved:
- `backend/requirements.txt` — add `APScheduler>=3.10`
- `backend/src/services/retention_service.py` — NEW
- `backend/src/main.py` — register scheduler in lifespan
- `backend/src/api/routes/admin.py` — NEW (or extend ingestion.py)
- `backend/src/database/models.py` — verify FKs have `ondelete='CASCADE'`;
  add if missing for `summaries`, `embeddings`, `entity_mentions` (last
  one will exist after milestone 6)
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — add `retention_dry_run`

Gotchas:
- APScheduler in async FastAPI: use `AsyncIOScheduler`, register in the
  lifespan handler.
- Don't delete during a request — the cron runs in a background job.
- Test with a fixed clock if possible (freezegun) to avoid flakes.
- The first production run should be dry-run; have a clear toggle.

## Out of scope
- Soft-delete / archive flow (PRD picked hard-delete)
- Different retention policies per source / category
- Restoring deleted articles
- Admin UI for running retention (CLI / curl is enough)

## Verification
```bash
# Insert an old article
sqlite3 backend/news.db "INSERT INTO articles (title, url, source, published_at, content)
  VALUES ('old', 'https://test.local/old', 'test', datetime('now', '-31 days'), 'old content');"

# Dry-run via admin route
curl -X POST 'http://localhost:8000/api/admin/retention/run?dry_run=true'
# Should list the 'old' article ID

# Live run
curl -X POST 'http://localhost:8000/api/admin/retention/run'

sqlite3 backend/news.db "SELECT COUNT(*) FROM articles WHERE url='https://test.local/old';"
# Should be 0

# E2E
python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-pipeline --skip-frontend
```

## Risks
- Cascade misconfigured → orphan rows or wrong-table deletes. Test with
  a copy of `news.db`, not the live one.
- Scheduler conflicts with the test runner if it fires during E2E. Mitigation:
  scheduler reads `ENVIRONMENT=test` and skips if set.
