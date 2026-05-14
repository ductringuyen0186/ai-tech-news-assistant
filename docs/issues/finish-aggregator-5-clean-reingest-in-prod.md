# [Chore] Wipe + clean re-ingest in production validates the live system end-to-end

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Chore                                                |
| Priority       | P1                                                   |
| Estimate       | S                                                    |
| Assignee       | unassigned                                           |
| Labels         | data-layer, devops, ops                              |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 5 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
After Milestones 1–4 land, the live deploy works but the production DB
still contains whatever was migrated up. A single command resets the
data layer: wipe `news.db`, run migrations, ingest fresh. This is also
a confidence check that the deploy + ingest + summarisation + retention
loop is internally consistent live.

## Description
**Today:** No standard "reset to fresh" path. Manual `rm news.db` +
restart works locally but is awkward on the VPS.

**After this change:** A single script (`scripts/reset_data.sh`) does
the right thing both locally and on the VPS. After running on the live
system, every tab has real data; tests against the live URL pass.

## Acceptance criteria
- [ ] `scripts/reset_data.sh` exists, is executable, accepts a `--prod`
      or env-var flag for live runs (extra confirm step on prod)
- [ ] The script wipes `news.db`, runs migrations to recreate schema,
      triggers `POST /api/ingest/` with `auto_summarize=true,
      background=false`, waits for completion, returns 0 on success
- [ ] After running, `GET /api/news/stats` returns `total_articles >= 50`
      (sanity bar; depends on RSS feed health that day)
- [ ] All articles have non-null `summary` (orchestrator ran)
- [ ] At least 5 articles have `summary_generated = TRUE` (AI summary
      step ran for some articles even if not all in the limit)
- [ ] New E2E test `live_ingest_smoke`: posts an ingest, polls until
      done, verifies article count went up
- [ ] Documentation in `docs/runbooks/reset-prod-data.md` explains when
      and how to run this; warns it's destructive

## Implementation notes
Files likely involved:
- `scripts/reset_data.sh` — NEW
- `docs/runbooks/reset-prod-data.md` — NEW
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — add
  `live_ingest_smoke`

Gotchas:
- The script must be safe to re-run (idempotent on the schema steps).
- On the VPS, the SQLite file lives in a Docker volume. The script needs
  to either run *inside* the backend container (`docker exec`), or the
  volume mount needs to be predictable.
- Don't run this during scheduled retention; check time-of-day or skip
  retention for the next cycle after a wipe.
- Confirmation prompt for `--prod`: refuse to run unless the user types
  the literal string `WIPE PROD`.

## Out of scope
- Restoring from a snapshot (handled by VPS provider tooling)
- Selective deletion (this is full wipe + reingest)
- Migration to a new schema (this assumes current schema is canonical)

## Verification

### Local
```bash
./scripts/reset_data.sh
curl http://localhost:8000/api/news/stats     # total_articles >= 50
python .claude/skills/test-app-e2e/scripts/run_e2e.py
```

### Production (only after Milestone 4 deploy)
```bash
ssh user@vps "cd /opt/news-aggregator && ./scripts/reset_data.sh --prod"
# follow confirmation prompt
curl https://news.<domain>.tld/api/news/stats   # total_articles >= 50
```

## Risks
- Wipe runs accidentally on prod → strong confirmation prompt; document
  in runbook; never make this an auto-trigger.
- Ingestion on the VPS is slower than at home (small CPU) → tolerate up
  to 5 minutes for the wait, surface progress via stdout.
- An RSS feed is down on the day of wipe → tolerate; if `total_articles
  < 50`, log a warning but don't fail (document in runbook).
