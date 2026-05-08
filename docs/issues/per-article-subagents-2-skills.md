# [Feature] Implement 4 agent skills wrapping existing services

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P0                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, agent, skills                                                 |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 2 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
Per-article subagents need a stable set of skills they can call. M2 implements 4 thin-wrapper skills around services that already exist (`SearchService`, `SummarizationService`, `EntityExtractionService`, knowledge-graph repository). Cache reuse for `summarize_article` is the only non-trivial logic.

## Description
**Today:** Existing services are called directly from `AgenticResearchService.run()`. There's no skill registry, no cache reuse for summarization at the agent level.

**After this change:** A new `services/agent_skills/` package contains 4 skills, each in its own file with a clear input/output schema:

1. **`search_articles(query: str, top_k: int = 5)`** — wraps `SearchService.search`. Returns a list of `{article_id, title, source, snippet, score}` dicts.

2. **`summarize_article(article_id: int, focus_question: str | None = None)`** — wraps `SummarizationService` PLUS cache reuse:
   - First check `articles.summary` for the given article
   - If summary exists AND (`focus_question is None` OR the cache key matches): return immediately as `{"summary": ..., "cache_hit": True, "article_id": ...}`
   - Otherwise: call `SummarizationService.summarize_content` with a focus-question-aware prompt, write back to `articles.summary`, return `{"summary": ..., "cache_hit": False, "article_id": ...}`

3. **`extract_entities(article_id: int)`** — wraps `EntityExtractionService.process_article`. Returns `{article_id, entities: [...], count: N}`.

4. **`query_knowledge_graph(entity_or_topic: str, depth: int = 1)`** — walks the entity/co-mention graph from M6. Returns `{nodes: [...], edges: [...]}` of co-occurring entities up to `depth` hops away.

Each skill is a pure async function. If M1's spike said GO on deepagents, each is also wrapped as a deepagents `Tool`/`Skill`. If NO-GO, each is registered in a custom dataclass-based `SkillRegistry`.

## Acceptance criteria
- [ ] `backend/src/services/agent_skills/__init__.py` exists and exports the 4 skill functions
- [ ] `backend/src/services/agent_skills/search_articles.py` calls `SearchService.search` and returns the documented shape
- [ ] `backend/src/services/agent_skills/summarize_article.py` honors cache reuse: returns `cache_hit=True` when applicable, generates and writes back when not
- [ ] `backend/src/services/agent_skills/extract_entities.py` calls `EntityExtractionService.process_article` and returns the documented shape
- [ ] `backend/src/services/agent_skills/query_knowledge_graph.py` walks the entity graph and returns the documented shape
- [ ] New unit tests in `backend/tests/unit/test_agent_skills.py` cover:
  - happy path for each skill (4 tests)
  - `summarize_article` cache hit (1 test)
  - `summarize_article` cache miss + write-back (1 test)
  - `query_knowledge_graph` with depth=1 returns ≥1 edge for an entity that has co-mentions (1 test)
- [ ] If M1 was GO: skills are also registered with deepagents and importable via the agent. If NO-GO: skills are in a `SkillRegistry` dataclass
- [ ] All 17 existing contract tests still pass
- [ ] All Ollama-calling skills (just `summarize_article`) use the existing `_ollama_call` logger pattern

## Implementation notes
Files likely involved:
- `backend/src/services/agent_skills/__init__.py` — NEW
- `backend/src/services/agent_skills/search_articles.py` — NEW
- `backend/src/services/agent_skills/summarize_article.py` — NEW
- `backend/src/services/agent_skills/extract_entities.py` — NEW
- `backend/src/services/agent_skills/query_knowledge_graph.py` — NEW
- `backend/src/repositories/article_repository.py` — minor: add `get_summary_only(article_id) -> str | None` for fast cache lookups
- `backend/tests/unit/test_agent_skills.py` — NEW

Gotchas:
- The cache-reuse heuristic for `summarize_article`: keep it simple. If `focus_question is None`, always reuse. If `focus_question` is set, regenerate. Don't try to be clever with prefix-matching on the question — that's a v2 concern.
- `query_knowledge_graph` may need a small repository helper if there isn't already a clean co-mentions query. Add it to `repositories/entity_repository.py` (or wherever entities live).
- Skills are pure async functions — they should NOT depend on a global database session. Each call gets its own session via the existing repository pattern.

## Out of scope
- M3's SubagentPool (skills are dispatched serially in M2 unit tests; concurrency is M3)
- M4's rewrite of `AgenticResearchService` to use these skills
- `fetch_full_article` and `list_sources` skills (deferred per PRD)

## Verification
- `pytest backend/tests/unit/test_agent_skills.py -v` exits 0 with all 7+ tests green
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend` exits 0 (17/17)
- Manual smoke (optional): a small script that imports each skill, calls it with sample inputs, and prints the result

## Risks
- The knowledge-graph walk in `query_knowledge_graph` may produce huge result sets if the seed entity is highly-connected. Cap with `top_k` limit; document in the docstring.
- `summarize_article`'s write-back to `articles.summary` is a state mutation during a research run. Make sure it only writes on cache MISS, not on hit. Asserted in tests.
