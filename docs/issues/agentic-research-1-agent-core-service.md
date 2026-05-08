# [Feature] Build AgenticResearchService that decomposes, searches, and synthesizes

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, llm, agent, ollama                                            |
| Linked PRD     | [docs/prds/agentic-research.md](../prds/agentic-research.md) — Milestone 1 |
| Linked design  | [docs/designs/agentic-research.md](../designs/agentic-research.md)     |

## Context
The Research tab is the most visibly fake feature in the app: it labels
itself "Agentic Research Mode" but runs a single semantic-search query and
renders an empty `0 results / 0 sources used` report. M1 lays down the
backbone of the real agent — a service that decomposes a question into 3-5
sub-questions, searches each one against the local corpus, and synthesizes
a structured markdown report with `[N]` citations. SSE streaming and the
HTTP route come in M2; this milestone is the agent core, end-to-end but
non-streaming first.

## Description
**Today:** No agent service exists. The Research tab calls
`/api/search/semantic` directly and shows a stub with `0` everywhere.

**After this change:** A new `AgenticResearchService` in
`backend/src/services/agentic_research_service.py` exposes a single
async-generator entry point `run(question: str)` that yields events of
shape `{type: "phase" | "token" | "done" | "error", data: ...}`. The
service:

1. Emits `phase: "Decomposing"`
2. Calls Ollama (`gpt-oss:20b`) with a strict JSON-output prompt to
   produce `{"sub_questions": [str, ...]}` (3-5 items)
3. Validates the JSON; on parse failure, retries once with a stricter
   prompt; if still bad, falls through to single-question mode using the
   original question
4. For each sub-question: emits `phase: "Searching (i/N)"` and runs the
   existing semantic-search internal helper, capturing top-K=5 hits
5. Emits `phase: "Synthesizing"`
6. Builds the synthesis prompt with the user's question + per-sub-question
   results + an instruction to emit a structured markdown report with
   inline `[N]` citations matching a numbered `## Sources Used` section
7. Calls Ollama (non-streaming for M1; M2 will swap to a token stream)
   and yields the assembled report as a single `phase: "done"` event

Sub-questions returning zero hits do NOT fail the run — the synthesis
prompt explicitly tells the model to write "Could not find data on X" for
those.

## Acceptance criteria
- [ ] `backend/src/services/agentic_research_service.py` exists with a
      class `AgenticResearchService` and an async-generator method
      `run(self, question: str)`
- [ ] `await` consuming `service.run("AI chip announcements this week")`
      yields, in order: one `phase: "Decomposing"`, one or more
      `phase: "Searching (i/N)"`, one `phase: "Synthesizing"`, and exactly
      one `phase: "done"`
- [ ] The decomposer's JSON output is parsed via a strict schema
      (`pydantic` or manual `json.loads` + key check). Invalid JSON
      triggers exactly one retry with a stricter prompt; if still invalid
      the service falls through to single-question mode and the run still
      completes
- [ ] The final assembled report is a non-empty string with at least one
      `[N]` citation marker AND at least one corresponding entry in a
      `## Sources Used` section
- [ ] A new unit test
      `backend/tests/unit/test_agentic_research_service.py` mocks the
      Ollama client and exercises: happy path, invalid-JSON-then-retry,
      invalid-JSON-fall-through, zero-hit sub-question
- [ ] All 16 existing contract tests still pass:
      `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`
- [ ] Service has a module-level docstring covering the loop semantics
      and retry behaviour; every Ollama call is wrapped in a context
      manager that logs `start / end / duration / token_count`

## Implementation notes
Files likely involved:
- `backend/src/services/agentic_research_service.py` — NEW, the service
- `backend/src/services/summarization_service.py` — read for the existing
  Ollama-call pattern; may extend or wrap to support arbitrary models
- `backend/src/services/embedding_service.py` (or wherever
  `/api/search/semantic` is implemented) — reuse the search internals as
  a Python-level helper, NOT via HTTP
- `backend/src/models/article.py` — likely add a Pydantic model for the
  SSE event shape (`AgentEvent`), used here and in M2
- `backend/tests/unit/test_agentic_research_service.py` — NEW

Gotchas:
- `gpt-oss:20b` is slow on CPU. Tests must mock Ollama; do NOT hit the
  real model in unit tests
- The decomposer's JSON-parse fallback path is the highest-risk surface.
  Cover it with explicit tests
- The semantic-search helper should be reachable as a Python call (not
  HTTP); look for the internal function in `embedding_service.py` and
  expose it if not already public
- Keep the service unaware of SSE or HTTP — that's M2's job. The async
  generator is the contract

## Out of scope
- The HTTP route and SSE plumbing (M2)
- Frontend changes (M3)
- Streaming tokens during synthesis (M2 swaps the synthesis call to a
  streaming variant)
- Cancel / disconnect detection (M2)
- Source-snippet inclusion in `## Sources Used` (decided in M4)

## Verification
- `pytest backend/tests/unit/test_agentic_research_service.py -v` exits 0
  with all four scenarios green
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`
  exits 0
- Manual smoke (optional): a small script in `scripts/` that imports the
  service, calls `run("AI chip announcements this week")` against the
  real Ollama, and asserts the final report contains `[1]` and a
  `## Sources Used` line. Skip in CI; documented in the docstring.

## Risks
- `gpt-oss:20b` JSON-output reliability — covered by 1-retry + fallback;
  unit tests pin the behaviour
- Reusing the semantic-search internals may require a small refactor to
  expose them as a Python helper. Keep the change minimal; do not break
  the existing `/api/search/semantic` route
