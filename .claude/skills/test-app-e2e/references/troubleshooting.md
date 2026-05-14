# Fixer Agent Reference: Failure Categories

The E2E runner tags each failure with a `suggested_fix_area`. These are
hand-off briefings — what to read first, what's likely wrong, what NOT to
touch. Keep fixes minimal and scoped to the failing test.

## backend-startup
The backend never came up or crashed during the request.

- Check `tail -50` of the uvicorn log first; the error is almost always the
  last traceback before the test ran.
- Common causes: missing env var (`SQLITE_DATABASE_PATH`, `DATABASE_URL`),
  port 8000 already in use, an import failure inside `src/main.py` after a
  recent edit, a corrupted SQLite file at the configured path.
- Don't blanket-disable middleware or routes to "make it boot" — that hides
  real problems. Find the import or config that broke.

## backend-routes-health
`/health` responded but with the wrong shape. The response should include
at minimum a top-level `status` field with value `healthy`, `degraded`, or
`unhealthy`.

- Look in `backend/src/api/routes/health.py` and the response model that
  feeds it. A recent refactor may have removed or renamed `status`.
- "degraded" is acceptable for individual sub-services (e.g., DB
  connectivity) and is not a failure of this test.

## backend-routes-news
A news route returned non-200 or the wrong response shape.

- For listing: response must be `{"data": [...], ...}` with `data` as a list.
- For stats: payload (under `data` or top-level) must include
  `total_articles` and `articles_with_summaries`.
- Common cause: SQLite path mismatch (the route reads from one DB, the
  ingestion writes to another). Confirm `SQLITE_DATABASE_PATH` and
  `DATABASE_URL` point at the same file.

## backend-routes-summarize
`/api/summarize/status` returned non-200 or missing fields.

- Look in `src/api/routes/summarization.py` and `src/services/summarization_service.py`.
- The response should have a `status` field (`healthy` / `degraded` /
  `unhealthy`) and a `provider` field. If the provider is `ollama` and
  status is `unhealthy`, that's an Ollama problem (see `ollama-setup`),
  not a backend bug — the test should still pass because the route works.

## backend-routes-ingest
`/api/ingest/status` failed.

- Look in `src/api/routes/ingestion.py`. The route imports
  `SummarizationOrchestrator` — if that import fails, this whole module
  won't load.

## backend-orchestrator
`POST /api/ingest/summarize-pending` failed, or it reported success but the
DB summary count didn't actually go up.

- Read `src/services/summarization_orchestrator.py` and
  `src/repositories/article_repository.py` (especially
  `get_articles_without_summary` and `mark_summary_generated`).
- If `requested > 0` and `summarized > 0` but DB unchanged, the writeback
  isn't committing. Check that `mark_summary_generated` is awaited.
- If `failed > 0`, the LLM call is throwing — check Ollama health and the
  service's exception handling.

## backend-cors
The backend didn't echo `Access-Control-Allow-Origin` for a request from
the frontend's origin. The frontend will fail to load data in the browser.

- Check `ALLOWED_ORIGINS` env var and the CORS middleware setup in
  `src/main.py`. The list must include the exact origin the frontend
  serves from (default Vite is `http://localhost:5173`).
- Don't set `allow_origins=["*"]` — that disables credentialed requests.

## frontend-startup
The frontend dev server is unreachable.

- Did the user run `npm install` and `npm run dev`?
- Vite usually picks port 5173, but will increment if taken; check the
  actual URL printed by `vite`.
- This is often "the user forgot to start it" — flag clearly rather than
  pretending the frontend is broken.

## ollama-setup
Ollama is not reachable, or no models are pulled.

- This is environment, not code. Don't edit anything in the repo.
- Tell the user: `ollama serve` in one terminal, `ollama pull llama3.2:1b`
  once. The default model is set in `backend/.env` via `OLLAMA_MODEL`.

## test-runner
The test itself crashed (exception inside the runner, not in the app).

- Read the traceback in `detail`. Likely the runner needs a small fix —
  e.g., the response shape changed in a way the test didn't anticipate.
- Don't change the app to make a buggy test pass. Fix the test.

---

## Heuristics for fixers

- **Start with the smallest reproduction.** Re-run the single failing
  test (`run_e2e.py` doesn't have a `-k` flag yet, but you can comment out
  other test calls in `run_all()` for one-off debugging).
- **Don't refactor.** Make the minimum change that flips the test green.
- **Verify the fix locally before reporting back.** Re-run the runner and
  confirm zero failures (or at least: the failure you owned is gone).
- **Look for cascading failures.** If `backend-startup` failed, every other
  test failed too — fix the startup issue and ignore the downstream noise.

## backend-routes-rag
`POST /api/rag/query` failed.

- Check `src/api/routes/rag.py` and `src/services/rag_service.py`.
- The pipeline depends on `SearchService` AND `SummarizationService` — failure
  may originate in either. The keyword fallback (`_fallback_keyword_search`)
  should kick in when vector search returns no results, so an empty-but-200
  response usually means the question didn't match anything in the DB.
- If the response shape is `{success, data: {answer, sources, ...}}`, the
  frontend's chat handler must unwrap `envelope.data` (not `envelope`).

## backend-routes-search
`POST /api/search/semantic` failed.

- Check `src/api/routes/search.py` and `src/services/search_service.py`.
- The route depends on `EmbeddingRepository`. If you see "unable to open
  database file", the chroma_db dir doesn't exist. Create it with
  `mkdir -p backend/data/chroma_db`.
- "no such table: article_embeddings" means embeddings were never generated;
  run `backend/scripts/manage_embeddings.py` (or wait for the orchestrator
  to populate them post-ingest).

## backend-routes-digest
`GET /api/digest/` failed.

- Check `src/api/routes/digest.py`. It does a few simple SQL queries against
  `news.db`. If the DB path is wrong or articles table is empty, the digest
  will still return a valid (but mostly empty) shape.
