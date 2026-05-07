# Reset prod data: wipe + clean re-ingest

> **Destructive.** This runbook empties the live `articles` table (and its
> dependent `embeddings` / `embedding_metadata` / `article_categories`
> rows), then runs a fresh ingest. Anyone reading the site during the
> window between the wipe and the end of the re-ingest sees an empty
> homepage.

## When to run

- After landing a schema-affecting migration where you'd rather start
  clean than try to backfill.
- When ingestion has been off for a while and the DB is full of stale
  links you don't want users to see.
- As a confidence check that the deploy + ingest + summarise loop is
  internally consistent on the live box (the original Milestone 5 use
  case).

## When NOT to run

- During the daily retention window. The cron is harmless but wastes
  Ollama cycles. Schedule the reset for a different hour.
- If you only want to delete a subset. There is no selective mode -
  this is total wipe.
- For schema migrations themselves. Those are handled by Alembic at
  startup; this script doesn't run migrations, it expects the schema
  to already be present (the FastAPI app creates tables on first
  request when missing).

## Prerequisites

- The script is checked in at `scripts/reset_data.sh` and must be
  executable (`chmod +x` already applied at commit time).
- Local mode: backend running on `http://localhost:8000`, Ollama on
  `:11434`.
- Prod mode: `PROD_URL` env var pointing at the live deploy
  (e.g. `https://news.example.com`). The backend must already be up.

## Local run

```bash
./scripts/reset_data.sh
```

Expected duration: seconds for the wipe + a few minutes for the ingest
+ summarisation pass. Watch for `DONE: <N> articles` at the end.

## Production run

The intended invocation is over SSH from your laptop:

```bash
ssh deploy@<vps-ip> \
  "cd /opt/news-aggregator && PROD_URL=https://news.example.com ./scripts/reset_data.sh --prod"
```

The script will print:

```
  !!  This will WIPE every article on the live deploy.  !!
      Type the literal phrase  WIPE PROD  to continue.
      Anything else aborts.
confirm>
```

Type `WIPE PROD` (no quotes) and press Enter. Any other input aborts
with exit code 1 and no DB writes happen.

Expected duration: 1 to 5 minutes on a small VPS. The CPU is the
bottleneck (Ollama running a 1B model). The script polls `/api/news/stats`
at the end and refuses to return success unless `total_articles >= 50`.
If RSS feeds are unhealthy that day you may see fewer; that's a
warning condition, not silently swallowed.

## Verification after run

```bash
curl https://news.example.com/api/news/stats
# Expect: data.total_articles >= 50
#         data.articles_with_summaries > 0
```

A spot check of three or four article URLs against the live frontend
catches the case where ingest succeeds but summarisation crashed.

## Rollback

There is no rollback inside the script. The wipe is committed before
the ingest starts, and the ingest is non-deterministic (RSS feed
contents change minute to minute), so a "before" snapshot can't be
reconstructed from the script's state.

If a reset goes wrong on prod:

1. Restore from the latest VPS provider snapshot. (DigitalOcean,
   Hetzner, etc all support point-in-time restores; this is the
   accepted DR path for this service.)
2. If no snapshot exists, accept the data loss and re-run the script
   on a green ingest day.

## Common failures and what they mean

| Output                                       | Meaning                                         |
|----------------------------------------------|-------------------------------------------------|
| `aborted: confirmation phrase did not match` | You typed something other than `WIPE PROD`.     |
| `backend unreachable at .../health`          | Backend is down. Bring it up first.             |
| `WARNING: Ollama not reachable`              | Local only. Ingest still runs, summaries fail.  |
| `ingest call failed (timeout=600s?)`         | Slow CPU. Re-run with `INGEST_TIMEOUT=1200`.    |
| `total_articles=N < required 50`             | Bad RSS day. Confirm by hand and decide.        |

## Implementation notes

- The wipe goes through `POST /api/admin/wipe?confirm=WIPE`, not direct
  SQLite, so it works whether the DB lives on disk or inside a Docker
  volume. The route is in `backend/src/api/routes/admin.py`.
- The route refuses to do anything unless `confirm=WIPE` is the literal
  string. Even if the script is hijacked, an attacker still needs to
  hit the admin endpoint with the correct query string and the reverse
  proxy admin allowlist.
- The script is idempotent. Running it twice in a row leaves the DB in
  the same state both times.
