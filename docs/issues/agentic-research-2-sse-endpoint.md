# [Feature] Expose AgenticResearchService over SSE at POST /api/research

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | S                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, sse, fastapi, api                                             |
| Linked PRD     | [docs/prds/agentic-research.md](../prds/agentic-research.md) — Milestone 2 |
| Linked design  | [docs/designs/agentic-research.md](../designs/agentic-research.md)     |

## Context
M1 produced the agent service as a non-streaming async generator. M2
exposes that generator over an HTTP SSE endpoint and adds the
operationally-important pieces: token-level streaming during synthesis,
keepalive frames so the connection doesn't time out on slow Ollama
generation, disconnect-detection that cancels the in-flight model call,
and a single-in-flight gate (HTTP 429 on a second concurrent submit).

## Description
**Today:** The Research tab calls `/api/search/semantic` directly. There
is no `/api/research` endpoint.

**After this change:** A new FastAPI router at
`backend/src/api/routes/research.py` adds `POST /api/research` that:

1. Accepts a JSON body `{"question": str}` (Pydantic validated)
2. Returns `text/event-stream` headers and a `StreamingResponse`
3. Drives `AgenticResearchService.run(question)` and forwards each event
   as one SSE frame: `data: <json-encoded event>\n\n`
4. Swaps the synthesis call inside the service from non-streaming to
   token-streaming, emitting `phase: "token"` events for each chunk; the
   final `phase: "done"` event still carries the full assembled report
5. Emits `: keepalive\n\n` every 10 seconds when no real event has been
   pending — prevents proxy / browser timeout during slow synthesize
6. Detects client disconnect (FastAPI `Request.is_disconnected` /
   `await request.is_disconnected()`) and cancels the in-flight Ollama
   generation cleanly — Ollama logs a cancellation, no zombies
7. Enforces single in-flight per process via an `asyncio.Lock` (or a
   simple boolean + `asyncio.Event`); a second concurrent POST returns
   HTTP 429 with body `{"detail": "Another research run is in flight"}`

The router is registered in `backend/src/api/routes/__init__.py` (or the
equivalent main router file).

## Acceptance criteria
- [ ] `POST /api/research` with JSON body `{"question": "..."}` returns
      `Content-Type: text/event-stream` and at least one `data: ` line
      within 5 seconds
- [ ] Each SSE frame is a discrete `data: <json>\n\n` block whose JSON
      payload matches the `AgentEvent` shape from M1
- [ ] Token-streaming works: while synthesis is running, the client
      receives multiple `phase: "token"` events before the final
      `phase: "done"` event
- [ ] A `: keepalive\n\n` line appears in the stream when no real event
      has been pending for 10s (testable by stubbing the service to sleep)
- [ ] Closing the SSE connection mid-run cancels the in-flight Ollama
      generation: a unit test with a stub generator that yields slowly
      asserts the generator's `finally` / cancel handler ran
- [ ] A second `POST /api/research` while one is already in flight
      returns HTTP 429 with the documented JSON body
- [ ] New contract test `test_research_sse_smoke` in
      `.claude/skills/test-app-e2e/scripts/run_e2e.py` opens the SSE
      stream via `urllib`, parses lines, and asserts at least one
      `phase` event arrives within 5s
- [ ] All 16 existing contract tests still pass:
      `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`

## Implementation notes
Files likely involved:
- `backend/src/api/routes/research.py` — NEW, the SSE route
- `backend/src/api/routes/__init__.py` (or `api/main.py`) — register the
  router under the `/api` prefix
- `backend/src/services/agentic_research_service.py` — extend to emit
  `phase: "token"` events during synthesis (Ollama streaming call)
- `backend/src/config/api.ts` is FRONTEND — leave for M3
- `frontend/src/config/api.ts` — frontend; M3 will add the endpoint there
- `.claude/skills/test-app-e2e/scripts/run_e2e.py` — NEW contract test
  function

Gotchas:
- FastAPI's `StreamingResponse` requires an async generator that yields
  `bytes` or `str`. Wrap each event in `f"data: {json.dumps(event)}\n\n"`
- SSE keepalive lines start with `:` (a comment frame). Don't `data: `
  them — that breaks `EventSource` parsing
- `await request.is_disconnected()` only resolves on a real TCP close;
  when running behind uvicorn locally it works, but if you ever proxy
  this through Caddy in prod, double-check `proxy_buffering off` is set
- The single-in-flight lock must be process-local. Don't reach for Redis
  — single-user app, single uvicorn worker
- Pin the Ollama call's `client.generate(..., stream=True)` interface
  carefully; the existing `summarization_service.py` calls it
  non-streaming, so the streaming path is new

## Out of scope
- Frontend SSE consumption (M3)
- Citation anchor post-processing (M4)
- The full Playwright SSE spec (M5) — this milestone only ships the
  stdlib contract test
- Configurable model selection — endpoint is hard-coded to
  `gpt-oss:20b` via the service

## Verification
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend`
  exits 0 (16 + 1 = 17 tests)
- Manual: `curl -N -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" -d '{"question":"test"}'`
  shows streaming `data: {...}` lines
- Manual: open one curl, then a second curl in another terminal — second
  returns HTTP 429
- Manual: open curl, ctrl-C it mid-stream, check Ollama logs show the
  generation cancelled

## Risks
- SSE proxy buffering — flagged in gotchas; document in the route
  docstring for prod-deploy time
- The `is_disconnected` poll may be lossy if the agent is in the middle
  of a synchronous Ollama call. Consider polling between yields, or
  wrapping the Ollama call in a cancellable task
- Pydantic v1 vs v2 quirks on `StreamingResponse` headers — use
  explicit `media_type="text/event-stream"`
