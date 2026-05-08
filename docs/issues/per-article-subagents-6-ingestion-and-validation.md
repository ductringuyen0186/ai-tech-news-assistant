# [Refactor+Test] Migrate ingestion summarization + final validation

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Refactor + Test                                                        |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, ingestion, tests, e2e                                         |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 6 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
Mission 2 promised one shared `summarize_article` skill for both ingestion-time AND research-time summarization. M2 implemented the skill; M6 wires it into the ingestion pipeline AND runs the final validation pass for the full mission.

## Description
**Today (after M5):** `services/summarization_orchestrator.py` calls `SummarizationService` directly at ingest time. The new `agent_skills.summarize_article` is only used by the research path (M4).

**After this change:**

1. `SummarizationOrchestrator._summarize_one(article)` (or its equivalent) calls `agent_skills.summarize_article(article_id, focus_question=None)` instead of constructing a `SummarizationRequest` and calling `SummarizationService.summarize_content` directly
2. The cache-reuse path is hit naturally — when ingestion summarizes a never-summarized article, cache_hit=False; the skill generates and writes back; subsequent research-time calls for that article return cache_hit=True
3. The migration is shipped behind a feature flag `USE_AGENT_SKILL_SUMMARIZATION` (default `True` after the smoke confirms parity; default `False` for one ingest run while the cutover is verified). After M6's smoke test passes, the flag stays `True` and the old code path is deleted
4. Final validation: live `research.live.spec.ts` updated to assert subagent events arrive during a real Ollama-backed run

## Acceptance criteria
- [ ] `SummarizationOrchestrator._summarize_one` calls `agent_skills.summarize_article` instead of `SummarizationService` directly
- [ ] `core/config.py` adds `use_agent_skill_summarization: bool = True` (env var override `USE_AGENT_SKILL_SUMMARIZATION`)
- [ ] When the flag is `False`, the old code path runs (preserved for emergency rollback)
- [ ] When the flag is `True`, ingestion uses the skill — verified by a unit test that mocks the skill and asserts it's called
- [ ] A smoke test (`backend/scripts/smoke_ingest_via_skill.py`) ingests a small RSS feed, summarizes the new articles, and asserts every article has a non-null `articles.summary` after the run
- [ ] All 17 contract tests pass
- [ ] All 6 integration tests pass
- [ ] All 6 `research.spec.ts` tests pass (5 from Mission 1 + 1 new from M5)
- [ ] `research.live.spec.ts` updated to assert subagent events arrive during a real run; the live spec passes when invoked
- [ ] After the smoke confirms parity, the OLD `SummarizationOrchestrator` direct-call code path is deleted (or marked TODO-DELETE-AFTER-2-WEEKS)

## Implementation notes
Files likely involved:
- `backend/src/services/summarization_orchestrator.py` — flip to skill call
- `backend/src/core/config.py` — add the flag
- `backend/scripts/smoke_ingest_via_skill.py` — NEW
- `backend/tests/unit/test_summarization_orchestrator.py` — add a flag-on test and a flag-off test
- `frontend/e2e/research.live.spec.ts` — add a `expect(subagentEvents).toBeGreaterThan(0)` style assertion

Gotchas:
- The summary writeback inside `summarize_article` must use the same `articles.summary` column the orchestrator already writes to, so cache reuse works across ingestion + research
- The `summarization_orchestrator` currently sets `summary_generated = True` on the article. The skill should preserve that side effect — confirm in tests
- Don't break the existing entity-extraction post-hook: after a summary is generated, the orchestrator currently calls `EntityExtractionService.process_article`. Make sure that still fires after the skill returns
- The `USE_AGENT_SKILL_SUMMARIZATION` flag is a graceful-rollback hatch. After M6 smoke passes, the flag itself stays in the codebase but defaults to `True` and the old path is deleted in a follow-up cleanup PR

## Out of scope
- M1-M5 work
- New skills beyond the 4 already shipped
- Performance benchmarking (PRD's success metrics live there, not here)

## Verification
- `pytest backend/tests/unit/test_summarization_orchestrator.py -v` exits 0
- `python backend/scripts/smoke_ingest_via_skill.py --feed-url <small RSS> --limit 5` produces ≥1 newly-summarized article
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend` exits 0 with 17/17
- `cd frontend && npx playwright test research.spec.ts` exits 0 with 6/6
- `cd frontend && npx playwright test research.live.spec.ts --grep @live` exits 0 with all live tests passing including the new subagent-event assertion

## Risks
- The skill's `focus_question=None` path needs to produce a summary that's good enough for the news feed UI (which currently shows it on cards). Verify the skill's default-prompt output has acceptable quality. Spot-check 5 newly-ingested articles after the cutover
- The feature flag adds complexity. Hard requirement: it's REMOVED in a follow-up cleanup within 2 weeks of this mission shipping
- The live integration test runs gpt-oss:20b end-to-end and is slow (~30-180s per test). Don't run it in the default suite; it's gated by `--grep @live` per the existing config
