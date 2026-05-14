# [Bug] Stale RSS-blurb summaries persist after Ollama summarisation

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Bug                                                  |
| Priority       | P2                                                   |
| Estimate       | S                                                    |
| Assignee       | unassigned                                           |
| Labels         | backend, summarisation, data-quality                 |
| Linked PRD     | -                                                    |
| Linked design  | docs/designs/post-ingest-summarisation.md            |

## Context
Articles ingested via `/api/ingest/` have their `summary` column pre-filled
with the first 500 chars of the RSS description (legacy behaviour). When
the post-ingest orchestrator runs Ollama on them, it should overwrite that
RSS blurb with the AI summary. Spot-checking the DB, several articles still
show the RSS blurb even though `summary_generated = TRUE`, which suggests
the writeback path is missing in one branch of the orchestrator.

## Description

### For bugs only
**Steps to reproduce:**
1. Run ingestion against a fresh `news.db`:
   `curl -X POST localhost:8000/api/ingest/ -d '{"background": false, "auto_summarize": true}' -H 'content-type: application/json'`
2. Wait for the orchestrator to finish (a few minutes).
3. Query the DB:
   `sqlite3 backend/news.db "SELECT id, summary FROM articles WHERE summary_generated=1 LIMIT 5;"`

**Expected:** `summary` column shows the AI-generated text (not the RSS
blurb).
**Actual:** A subset of rows still show the RSS description verbatim.

## Acceptance criteria
- [ ] After running the orchestrator over an article whose RSS blurb is
      currently set, the `summary` column contains the AI-generated text,
      NOT the original blurb
- [ ] `summary_generated` is `TRUE` only when the AI summary was actually
      written (not when the article was skipped for being too short)
- [ ] A new unit test in `backend/tests/services/` exercises the writeback
      path and asserts the final DB state

## Implementation notes

Files likely involved:
- `backend/src/services/summarization_orchestrator.py` — `_summarize_one`
  is the writeback site; check both the success and skip-short branches
- `backend/src/repositories/article_repository.py` — `mark_summary_generated`
  writes the new summary; confirm the column is being passed through
- `backend/tests/services/` — add `test_orchestrator_overwrites_blurb.py`

Gotchas:
- The skip-short branch (content < 200 chars) currently calls
  `mark_summary_generated(id, summary=None)` — that's intentional. Don't
  "fix" it by writing the blurb back.
- `summary_generated` is the source of truth for "AI summary done" — empty
  `summary` text is OK for short articles.

## Out of scope
- Re-running summarisation on already-marked articles (separate issue if
  needed)
- Changing the RSS blurb pre-fill behaviour itself

## Verification
- Run the new unit test: `pytest backend/tests/services/test_orchestrator_overwrites_blurb.py -v`
- Manual: repro steps above; the bad rows should now show AI text
- Re-run the E2E suite: `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`
  — should still be 12/12 (or 13/13 with frontend up)

## Risks
- Touches the writeback path that's currently in production - test against
  a copy of `news.db` first, not the live one
