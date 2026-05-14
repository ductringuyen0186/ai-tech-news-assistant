# [Chore] Clean up stale tests and dead code so the repo reads cleanly

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Chore                                                |
| Priority       | P1                                                   |
| Estimate       | S                                                    |
| Assignee       | unassigned                                           |
| Labels         | repo-quality, tests, cleanup                         |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 1 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
After the dual-architecture cleanup, three test files still import the
removed `utils` package and break `pytest --collect-only`. There's also
leftover commented-out code from earlier refactors. The backend audience
will read this code — first impression matters. Get the repo to a state
where pytest runs clean and there are no obvious dead-code smells.

## Description
**Today:** `pytest backend/tests/ --collect-only` errors on three files
(`test_ingestion_integration.py`, `test_ci_environment.py`, and one E2E
test) because they import from the deleted `backend/utils/` package. The
13 E2E tests in the new suite cover the same ground.

**After this change:** All three stale tests removed. Remaining tests
collect and run cleanly. A pass through `backend/src/` removes
commented-out function bodies and orphaned imports.

## Acceptance criteria
- [ ] `pytest backend/tests/ --collect-only` exits 0 with no import errors
- [ ] `grep -rn "from utils\." backend/src` returns empty
- [ ] No commented-out function definitions (`# def foo`, `# async def bar`)
      remain in `backend/src/`
- [ ] All 13 E2E tests still pass:
      `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-pipeline --skip-frontend`
- [ ] `git diff --stat` shows only deletions and small import-line edits;
      no behavioural changes

## Implementation notes
Files likely involved:
- `backend/tests/integration/test_ingestion_integration.py` — delete
- `backend/tests/unit/test_ci_environment.py` — delete
- `backend/tests/e2e/test_complete_workflows.py` — delete (covered by new E2E suite)
- `backend/src/services/news_service.py` — has a redundant duplicate
  code path (the `summaries_count` rename experiment surfaced this)
- Any `__init__.py` that still references deleted modules

Gotchas:
- Don't delete tests that pass — only the ones that fail collection.
- The `migration_service.py` and `sqlalchemy_repository.py` files are
  unused but functional. Leave them for now (separate issue if pruning).
- Don't add new tests in this issue — that's other milestones' work.

## Out of scope
- Adding new tests
- Refactoring code structure
- Documentation rewrites

## Verification
```bash
cd backend
pytest tests/ --collect-only       # must exit 0
pytest tests/ -q                    # must pass (or skip cleanly)
cd ..
python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-pipeline --skip-frontend
```
All three commands exit 0.

## Risks
- A stale test that *was* passing might be deleted by accident — verify
  each one is actually broken before removing.
