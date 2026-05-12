# [Feature] Saved research (backend + frontend) + LLM-driven follow-up suggestions

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, backend, persistence, llm                                    |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 5           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
Two of the three engagement features ship in this milestone: saved research (backend-persisted) and follow-up suggestions (template-first; LLM if quality is poor).

## Description

### Part A — Saved research backend

1. New table via `database/init_db.py` (or wherever schema is declared):
   ```sql
   CREATE TABLE IF NOT EXISTS saved_research (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     question TEXT NOT NULL,
     report_md TEXT NOT NULL,
     sources_json TEXT NOT NULL,
     created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
   );
   ```
   With `CREATE TABLE IF NOT EXISTS` guard. Test against fresh + existing news.db
2. `models/saved_research.py` — Pydantic models (Create, Read, ReadList)
3. `repositories/saved_research_repository.py` — DAL methods: `create`, `list_all`, `get_by_id`, `delete_by_id`
4. `api/routes/saved_research.py` — 4 endpoints:
   - `POST /api/saved-research` body `{question, report_md, sources}` → returns full record
   - `GET /api/saved-research` returns list (id, question, created_at, ordered by created_at desc, capped at 100)
   - `GET /api/saved-research/{id}` returns full record
   - `DELETE /api/saved-research/{id}` removes
5. Register router in `api/routes/__init__.py`
6. Add to `frontend/src/config/api.ts`:
   ```ts
   savedResearch: "/api/saved-research",
   savedResearchById: (id: number) => `/api/saved-research/${id}`,
   ```

### Part B — Frontend Save button + Saved list

1. Save button on a completed research report (next to Copy markdown / Download .md). Click → POST → success toast → button flips to "Saved ✓" (disabled state)
2. New `SavedResearchList.tsx` rendered as the Saved sidebar tab:
   - List of saved reports: question + relative time + delete icon
   - Click row → opens the report (renders MarkdownReport with the saved markdown)
   - Delete icon → DELETE → row removed
3. Empty state: "No saved research yet. Run a query and click Save."

### Part C — Follow-up suggestions (template-first)

After a research run completes, render 3 follow-up suggestions BELOW the report. Source order of preference:

1. **Template-based v1** (default):
   - Extract entities from the report (regex: `\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b` filtered against common words)
   - Build 3 follow-ups using templates:
     - `"How is {entity_1} positioned vs the rest of the market?"`
     - `"What are the most recent developments around {entity_2}?"`
     - `"Drill into {entity_3}'s funding history."`
2. **LLM-based v2 fallback** (if user accepts in M5 review):
   - One extra Ollama call after synthesis with a prompt like `"Given this report, suggest 3 short follow-up research questions. Output JSON: ['...', '...', '...']"`
   - Adds ~5-10s to the run; gate behind a `USE_LLM_FOLLOWUPS` feature flag

Click any follow-up → fills input + fires research run.

## Acceptance criteria
- [ ] `saved_research` table created via init_db; works on fresh AND existing news.db
- [ ] 4 backend endpoints (POST, GET, GET-by-id, DELETE) with unit tests in `tests/unit/test_saved_research.py`
- [ ] Pydantic models + repository pattern matches the existing codebase style
- [ ] Frontend Save button POSTs on click; shows success toast; flips to "Saved ✓"
- [ ] Saved sidebar tab lists saved reports with question + relative time + delete
- [ ] Click row → renders report; Delete icon → removes
- [ ] Empty state shown when no saved reports
- [ ] 3 follow-up suggestions render below every completed research report
- [ ] Click follow-up → input filled + research run
- [ ] New Playwright test: `saved-research.spec.ts` covers the full Save → list → open → delete flow
- [ ] New Playwright assertion: follow-up suggestions render with ≥3 items after a completed run
- [ ] All existing tests still pass

## Implementation notes
Files:
- `backend/src/database/init_db.py` — add table DDL
- `backend/src/models/saved_research.py` — NEW
- `backend/src/repositories/saved_research_repository.py` — NEW
- `backend/src/api/routes/saved_research.py` — NEW
- `backend/src/api/routes/__init__.py` — register router
- `backend/tests/unit/test_saved_research.py` — NEW
- `frontend/src/config/api.ts` — add endpoints
- `frontend/src/components/SavedResearchList.tsx` — NEW
- `frontend/src/components/SuggestedFollowUps.tsx` — NEW
- `frontend/src/components/ResearchMode.tsx` — Save button + follow-ups
- `frontend/src/components/Sidebar.tsx` — add Saved entry (from M1)
- `frontend/e2e/saved-research.spec.ts` — NEW

Gotchas:
- The `sources_json` column stores the sources list as JSON text. Use `json.dumps` / `json.loads` at the repository layer; the API hands back/accepts native objects
- Cap saved_research at 100 rows: in the POST handler, if count > 100, delete the oldest before inserting. Document in the API spec
- For follow-up extraction, the regex-based entity extraction will produce noise; filter against a stopword list (top 50 common English words) + skip single-letter matches
- The Saved sidebar tab is BELOW the 6 main tabs visually (or in a separate group). Sidebar from M1 has space for it

## Out of scope
- LLM-driven follow-up suggestions (defer to v2, but the spike is in this milestone if time permits)
- Sharing saved research via URL
- Editing saved reports
- Tagging / organizing saved reports

## Verification
- `cd backend && pytest tests/unit/test_saved_research.py -v` — all pass
- `cd frontend && npx playwright test saved-research.spec.ts` — full flow passes
- Manual: run a research query, click Save, navigate to Saved tab, open the saved report, delete it
- Manual: run a research query, click a follow-up chip, verify input fills and run starts

## Risks
- Template-based follow-up extraction can produce nonsense if the report is light on capitalized entities. Have a fallback: if extraction returns <3 entities, use 3 hardcoded "broaden the scope" templates
- Saved research can grow without bound on long-term use. The 100-row cap mitigates
- Backend table migration on existing news.db is the main risk surface — test explicitly
