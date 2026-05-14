# [Feature] Persist user settings server-side via /api/settings

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Feature                                              |
| Priority       | P0                                                   |
| Estimate       | M                                                    |
| Assignee       | unassigned                                           |
| Labels         | backend, frontend, data-layer                        |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 2 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
Settings (selected categories, view mode) only live in localStorage today.
Open the app in a different browser, the settings vanish. The maintainer
flagged this as the worst-offender feature for portfolio quality. Move the
source of truth to the backend; localStorage becomes a cache.

## Description
**Today:** `App.tsx` reads/writes `localStorage["techpulse_categories"]`.
No backend endpoint exists.

**After this change:** A `Settings` table (single-row, single-user)
persists categories + view preferences. New endpoints `GET /api/settings`
and `PUT /api/settings` round-trip JSON. Frontend fetches on mount, saves
on the existing "Save preferences" button click.

## Acceptance criteria
- [ ] New `Settings` SQLAlchemy model + migration adds `settings` table
      (id, categories JSON, view_mode, show_trending_only, updated_at)
- [ ] `GET /api/settings` returns `{success, data: {categories, view_mode, ...}}`
      with HTTP 200 even on first call (returns sensible defaults if no row)
- [ ] `PUT /api/settings` with a valid body persists, returns the saved
      shape, subsequent `GET` returns the new value
- [ ] `App.tsx` `useEffect` on mount calls `GET /api/settings`, sets state
- [ ] `TopicFilter.onSave` calls `PUT /api/settings` instead of (or in
      addition to) localStorage
- [ ] localStorage usage is allowed only as an offline cache; on every
      mount the backend value wins
- [ ] New E2E test `settings_persistence`: PUT a value, GET it back,
      assert equality
- [ ] Manual check: change a category, refresh the browser, the change
      is preserved

## Implementation notes
Files likely involved:
- `backend/src/database/models.py` — add `Settings` SQLAlchemy model
- `backend/src/repositories/settings_repository.py` — NEW (CRUD on the row)
- `backend/src/services/settings_service.py` — NEW (validation, defaults)
- `backend/src/api/routes/settings.py` — NEW (`GET`, `PUT`)
- `backend/src/api/routes/__init__.py` — register the route
- `backend/src/models/api.py` (or similar) — Pydantic models for request/response
- `frontend/src/App.tsx` — replace localStorage-as-truth with `apiFetch`
- `frontend/src/config/api.ts` — already has `settings` slot? Add if missing
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — add `settings_persistence` test

Gotchas:
- Single-row table: use a fixed `id=1` upserted on every PUT, or add a
  primary key constraint that's just `singleton`. Don't allow > 1 row.
- The frontend already has working save logic in `App.tsx`; rip out the
  localStorage-as-truth path, keep localStorage as a fallback for offline.
- Don't break the existing 13 E2E tests — settings is additive.

## Out of scope
- Per-user settings (single-user app; one row total)
- Auth-gated settings (no auth in this project)
- Real-time push of settings across tabs (refresh-on-mount is enough)
- Settings UI improvements beyond wiring the existing controls

## Verification
```bash
# Backend round-trip
curl -X PUT http://localhost:8000/api/settings \
  -H 'content-type: application/json' \
  -d '{"categories":["AI","Robotics"],"view_mode":"detailed"}'
curl http://localhost:8000/api/settings   # should reflect the PUT

# E2E
python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-pipeline --skip-frontend

# Manual: open frontend, change topic filter, refresh, confirm persisted
```

## Risks
- Frontend already-saved localStorage values may shadow the backend value
  on first mount — clear them or migrate them on first run
