# [Feature] Replace Knowledge Graph mock with real entity extraction from articles

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Feature                                              |
| Priority       | P0                                                   |
| Estimate       | L                                                    |
| Assignee       | unassigned                                           |
| Labels         | backend, frontend, ml, ai                            |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 6 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
Knowledge Graph tab currently shows hardcoded mock data. Recruiter clicks
it, sees fake "OpenAI ↔ Anthropic ↔ Google" edges, immediately knows
it's a stub. This is the heaviest milestone — real named-entity
extraction, persistence, API, and frontend rewire. The maintainer chose
this option explicitly during grilling.

## Description
**Today:** `KnowledgeGraph.tsx` uses a hardcoded `mockData` object.
There's no entity extraction or `/api/knowledge-graph` endpoint.

**After this change:** Each article goes through an entity-extraction
service after summarisation. Named entities (companies, people, products,
technologies) get persisted in `entities` + `entity_mentions` tables.
A new endpoint serves top-N entities + co-mention edges. The frontend
calls it; the mock is gone.

## Acceptance criteria
- [ ] New SQLAlchemy models: `Entity` (id, name, type, mention_count,
      created_at) and `EntityMention` (article_id, entity_id, position)
- [ ] Migration applies on app startup
- [ ] New `EntityExtractionService` uses Ollama (prompt-based: "extract
      named entities, return JSON") with sanity rules:
      - Reject strings under 3 chars
      - Reject strings that are all-uppercase non-acronyms (≥ 5 chars
        all-caps)
      - Reject common English stopwords ('the', 'and', etc.)
      - Reject single common words ('news', 'tech', 'company')
      - Type tagged as one of `company | person | product | technology |
        other`
- [ ] Service runs as a post-summarisation hook in the orchestrator (or
      as a separate background job; pick one in implementation)
- [ ] `GET /api/knowledge-graph?limit=50` returns
      `{nodes: [{id, name, type, mention_count}], edges: [{source, target,
      weight}]}` where edges are entities co-mentioned in ≥ 2 articles
- [ ] Frontend `KnowledgeGraph.tsx`:
      - Calls the endpoint on mount
      - Removes ALL hardcoded mock data
      - Renders nodes + edges via the existing canvas code
      - Tolerates 50+ nodes (zoom + pan controls work; if missing, add
        simple zoom-via-scroll)
- [ ] New E2E tests:
      - `kg_endpoint`: returns valid `{nodes, edges}` shape with > 0 nodes
        after a fresh ingest
      - `kg_no_mock`: `grep -rn "mockData\|hardcoded" frontend/src/components/KnowledgeGraph.tsx`
        returns empty (no static fallback in production code path)
- [ ] Manual: load the live URL, click Knowledge Graph tab, see real
      entity names from this week's articles

## Implementation notes
Files likely involved:
- `backend/src/services/entity_extraction_service.py` — NEW
- `backend/src/repositories/entity_repository.py` — NEW
- `backend/src/api/routes/knowledge_graph.py` — NEW
- `backend/src/api/routes/__init__.py` — register
- `backend/src/database/models.py` — add `Entity`, `EntityMention`
- `backend/src/services/summarization_orchestrator.py` — call entity
  extraction after summarisation (optional: separate job)
- `frontend/src/components/KnowledgeGraph.tsx` — rewire
- `frontend/src/config/api.ts` — add `knowledgeGraph` endpoint slot
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — add 2 tests

Gotchas:
- **Ollama prompt for NER**: 1B models hallucinate aggressively. Use a
  strict JSON-output prompt with examples. Validate the output is parseable
  JSON before persisting; reject silently on parse failure.
- **Sanity rules are crucial**: without them, the graph fills with garbage
  like 'AI', 'TODAY', 'NEW' — every recruiter will spot this.
- **Co-mention edges**: a pair of entities that appear in the same article
  count as 1; weight = number of articles where both appear.
- **Performance**: don't call Ollama serially for 80 articles in one
  request (that's 13 minutes on CPU). Either:
  - Call once per article during ingest (amortised cost), OR
  - Run as a separate `/api/admin/extract-entities` background job
- **Cascade**: when retention deletes an article, related `entity_mentions`
  must cascade. After cascading, prune `entities` rows whose `mention_count`
  drops to 0 (separate tiny query in the retention service).
- **Top-N limit on the API**: 50 is the default; never return all entities
  — the canvas can't render thousands.

## Out of scope
- Sentiment / relationship typing on edges (just co-mention for v1)
- Disambiguation (e.g., "Apple" the company vs "apple" the fruit)
- Entity merging (typo / case variants are different entities for v1;
  optional cleanup later)
- Sophisticated graph layout algorithms — the existing canvas is fine
- Real-time updates as new articles ingest — refresh on tab open is enough

## Verification
```bash
# After ingest + summarisation completes
curl http://localhost:8000/api/knowledge-graph?limit=20 | python -m json.tool
# Should have non-empty nodes; each node has id, name, type, mention_count

# Verify mock is gone
grep -rn "mockData" frontend/src/components/KnowledgeGraph.tsx
# Should return empty

# E2E
python .claude/skills/test-app-e2e/scripts/run_e2e.py

# Manual
# Open frontend, click Knowledge Graph, see real entity names from this
# week's headlines (companies like NVIDIA, OpenAI, etc., based on actual
# articles in the DB)
```

## Risks
- **Ollama returns garbage entities** → sanity rules + JSON validation
  + reject-on-parse-fail. Log rejected outputs for tuning.
- **Canvas doesn't scale to 50+ nodes** → API limits; if rendering is
  still slow, add filter-by-type controls in the frontend.
- **Prompt drift between local and prod Ollama versions** → pin the
  Ollama model version (`llama3.2:1b@<digest>`) in env; document in PRD.
- **Slow** → cache the response (entities only change after a new ingest);
  invalidate on ingest completion.
