# deepagents API Surface — Mission 2 Integration Notes

| Field      | Value                                                              |
|------------|--------------------------------------------------------------------|
| Status     | M1 spike complete — adoption is the path forward                   |
| Author     | M1 worker (Mission 2)                                              |
| Date       | 2026-05-08                                                         |
| Package    | `deepagents==0.5.7` (PyPI: <https://pypi.org/project/deepagents/>) |
| Companion  | `langchain-ollama==1.1.0` (`ChatOllama` adapter)                   |
| Spike      | `backend/scripts/spike_deepagents.py`                              |
| Verdict    | **GO**                                                             |

This document is the **API-surface reference** for the M2-M6 workers.
It is not a go/no-go evaluation — the user pre-confirmed adoption.
Treat it as the cheat-sheet for "how do I do X with deepagents in
this codebase" — every section has a copy-pasteable code snippet.

---

## 1. Installation

The M1 spike pinned the following in `backend/requirements.txt`:

```text
# deepagents agent runtime (Mission 2 - per-article subagents)
deepagents==0.5.7
langchain-ollama>=1.1.0  # ChatOllama adapter for local Ollama
```

The install pulls in (and upgrades) `langchain==1.2.18`,
`langchain-core==1.3.3`, `langgraph==1.1.10`, `langgraph-prebuilt==1.0.13`
plus a few transitive provider SDKs (`langchain-anthropic`,
`langchain-google-genai`). These are pulled by `deepagents` even when
unused — they are import-only and don't run.

**Python 3.13 compatibility:** clean. The user's interpreter
(`C:\Users\Tri\AppData\Local\Programs\Python\Python313\python.exe`)
installed every dep without a build step. No wheel issues.

**Existing-stack collision check:** `langchain==1.2.0` was already in
the user's env from the chroma stack and got upgraded to 1.2.18 by
deepagents. No breaking import changes — the contract suite still
collects and the backend still serves `/health` after a restart.

---

## 2. Constructing an Agent

The single entry point is `deepagents.create_deep_agent`. It returns
a `langgraph.graph.state.CompiledStateGraph` (LangGraph compiled
StateGraph), which is the runtime object you call.

```python
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://localhost:11434",
    temperature=0.2,
    num_predict=512,
)

@tool
def search_articles(query: str, limit: int = 3) -> str:
    """Semantic-search the local tech-news corpus.

    Args:
        query: Natural-language search query.
        limit: How many top hits to return (1-10).

    Returns:
        JSON string with shape {"results": [{...}, ...]}.
    """
    ...  # body — see section 3 below

agent = create_deep_agent(
    model=llm,
    tools=[search_articles],
    system_prompt="You are a research assistant ...",
)
```

Key notes:

- **`model`** accepts either a `BaseChatModel` instance (what we use)
  or a `"provider:model"` string. We always pass a pre-built
  `ChatOllama` so the base URL stays explicit.
- **`tools`** is merged with deepagents' built-in tools
  (`write_todos`, `ls`, `read_file`, `write_file`, `edit_file`,
  `glob`, `grep`, `execute`, `task`). For Mission 2 we
  *want* most of those gone — see "Trimming the default tool stack"
  below.
- **`system_prompt`** is prepended to the SDK's default deep-agent
  prompt. It does NOT replace it. To get a fully-custom prompt you'd
  need to use a `HarnessProfile` (out of scope for M2).
- **`subagents`** is the M3 hook — see section 6.

### Trimming the default tool stack (M4 will need this)

The default deep-agent ships with filesystem + shell + todo tools that
we don't want exposed when the agent is talking to end-users. Two
options:

1. **System-prompt instruction** ("Do NOT use the filesystem or todo
   tools"). The spike does this. Good enough for M1; the model
   complies for `gpt-oss:20b`.
2. **`general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)`**
   on a registered `HarnessProfile` (drops the `task` tool entirely).
   Combine with a custom `excluded_middleware` list to drop
   `FilesystemMiddleware` etc. — for M4, this is the cleaner path.

For M4 we will likely register a custom `HarnessProfile` that excludes
`FilesystemMiddleware` and `TodoListMiddleware` and disables the
default general-purpose subagent. Document the exact recipe when M4
lands.

---

## 3. Registering Tools / Skills

deepagents accepts any LangChain `BaseTool`. The path of least
resistance is the `@tool` decorator from `langchain_core.tools`:

```python
from langchain_core.tools import tool

@tool
def search_articles(query: str, limit: int = 3) -> str:
    """One-line summary the LLM reads VERBATIM.

    Args:
        query: ...   <-- becomes input schema
        limit: ...

    Returns:
        ...
    """
    return some_json_string
```

Important rules the M2 worker must follow:

- **The docstring is the schema.** LangChain's `infer_schema=True`
  (default) builds a JSON schema from the function signature plus
  the Google-style `Args:` block. Keep arg descriptions tight.
- **Return a string.** The LLM only sees text. Return `json.dumps({...})`
  for structured payloads — the M4 orchestrator will parse them on
  the way back up.
- **Sync wrapping for async services is fine.** Our `SearchService.search`
  is async. The spike wraps it in `asyncio.run(_run())` inside the
  sync `@tool` body. LangGraph runs sync tools via `to_thread`, so
  wrapping is non-blocking from the agent's perspective.
- **Side-effect logging works.** The spike appends to a module-level
  list inside the tool body and reads it after the run. M4 will
  replace this with an SSE event emitter.

### Explicit Pydantic schema (when you need precision)

If the inferred schema is wrong (e.g. you want enums, regex
constraints), pass `args_schema`:

```python
from pydantic import BaseModel, Field

class SearchArticlesInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=3, ge=1, le=10)

@tool("search_articles", args_schema=SearchArticlesInput)
def search_articles(query: str, limit: int = 3) -> str:
    """Semantic-search the local tech-news corpus."""
    ...
```

The M2 worker should use the explicit-schema form for
`summarize_article` (which has the `focus_question: Optional[str]`
gotcha around cache hits) and `query_knowledge_graph` (which takes a
structured filter).

### Async tools

`@tool` decorates async functions just as well. Pattern when the M2
worker has no sync wrapper available:

```python
@tool
async def summarize_article(article_id: str, focus_question: str | None = None) -> str:
    """..."""
    return await _do_async_work(...)
```

LangGraph dispatches async tools natively (no `to_thread`).

---

## 4. Wiring to Local Ollama

`langchain-ollama`'s `ChatOllama` is the adapter. The spike wires it
in three lines:

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://localhost:11434",  # MUST match settings.ollama_host
    temperature=0.2,
    num_predict=512,    # cap output length
    num_ctx=8192,       # optional - default is model card value
)
```

Tool-calling support: **`gpt-oss:20b` supports Ollama's native tool
calling.** Verified directly via `POST /api/chat` with a
`tools=[{type:"function",...}]` payload — the model returns
structured `tool_calls` entries with valid JSON arguments.
Tested round-trip: simple "What is 2+2? Use the calculator tool" →
model emits `{"name":"calculator","arguments":{"a":2,"b":2}}`.

### Reading settings (M4 wiring)

In production we want `base_url` to come from
`backend/src/core/config.py:Settings.ollama_host` (same source as
`AgenticResearchService` today):

```python
from src.core.config import get_settings

settings = get_settings()
llm = ChatOllama(
    model=settings.ollama_model or "gpt-oss:20b",
    base_url=settings.ollama_host or "http://localhost:11434",
    temperature=0.2,
)
```

### Timeouts

`ChatOllama` accepts `client_kwargs={"timeout": 60}` to set the
underlying httpx timeout. Use this — the existing
`AgenticResearchService` honours `settings.ollama_timeout` (default
60s), so M4 should pass the same value:

```python
llm = ChatOllama(
    model=...,
    base_url=...,
    client_kwargs={"timeout": settings.ollama_timeout or 60},
    async_client_kwargs={"timeout": settings.ollama_timeout or 60},
)
```

---

## 5. Receiving Tool-Call Events (the SSE-bridge pattern)

This is **the most important section for M4.** The compiled deep
agent exposes three async drains:

1. `agent.ainvoke(inputs, config=...)` — returns the final state
   only. No streaming. NOT suitable for SSE.
2. `agent.astream(inputs, config=...)` — yields per-node state
   updates. Useful for coarse progress, not for tool-boundary
   events.
3. **`agent.astream_events(inputs, config=..., version="v2")`** —
   yields LangChain's v2 event stream. This is what M4 uses.

```python
async for ev in agent.astream_events(inputs, config=config, version="v2"):
    kind = ev.get("event")
    if kind == "on_tool_start":
        # ev["name"] == tool name, ev["data"]["input"] == args dict
        ...
    elif kind == "on_tool_end":
        # ev["data"]["output"] == ToolMessage with .content (string)
        ...
    elif kind == "on_chat_model_stream":
        # ev["data"]["chunk"] == AIMessageChunk; chunk.content has tokens
        ...
    elif kind == "on_chat_model_end":
        # FINAL assistant message (or any non-final one if there were
        # multiple model turns). The LAST one is the agent's answer.
        ...
```

Event kinds we care about (verified in spike):

| Event kind             | When fired                              | Data we extract                                     |
|------------------------|-----------------------------------------|-----------------------------------------------------|
| `on_chat_model_start`  | Each LLM turn begins                    | (mostly metadata; not used)                         |
| `on_chat_model_stream` | Each token chunk (if streaming enabled) | `data.chunk.content` (string, may be empty)         |
| `on_chat_model_end`    | Each LLM turn ends                      | `data.output.content` (full assistant message text) |
| `on_tool_start`        | Tool call dispatched                    | `name`, `data.input` (kwargs dict)                  |
| `on_tool_end`          | Tool returned                           | `data.output.content` (the string the tool returned)|

### The M4 SSE bridge — concrete sketch

Our existing `AgenticResearchService.run` is an
`AsyncGenerator[Dict[str, Any], None]` that yields `AgentEvent`-shaped
dicts (`{"type": "phase"|"token"|"error"|"done", "data": ...}`).
M4 keeps that contract and adds two new types: `subagent: start` and
`subagent: done`. The bridge is a thin translation layer:

```python
async def run(self, question: str) -> AsyncGenerator[Dict[str, Any], None]:
    yield {"type": "phase", "data": "Planning"}

    inputs = {"messages": [{"role": "user", "content": question}]}
    config = {"recursion_limit": 24}

    final_text = ""
    async for ev in self._agent.astream_events(inputs, config=config, version="v2"):
        kind = ev.get("event")

        if kind == "on_tool_start":
            yield {
                "type": "subagent",
                "data": "start",
                "tool": ev.get("name"),
                "args": ev.get("data", {}).get("input"),
            }
        elif kind == "on_tool_end":
            output = ev.get("data", {}).get("output")
            content = getattr(output, "content", "") if output else ""
            yield {
                "type": "subagent",
                "data": "done",
                "tool": ev.get("name"),
                "result_size": len(content) if isinstance(content, str) else 0,
            }
        elif kind == "on_chat_model_stream":
            chunk = ev.get("data", {}).get("chunk")
            text = getattr(chunk, "content", "") if chunk else ""
            if isinstance(text, str) and text:
                yield {"type": "token", "data": text}
        elif kind == "on_chat_model_end":
            output = ev.get("data", {}).get("output")
            content = getattr(output, "content", None) if output else None
            if isinstance(content, str) and content.strip():
                final_text = content

    yield {"type": "phase", "data": "done", "report": final_text}
```

**Cancellation:** `astream_events` is a vanilla async generator. If
the SSE consumer disconnects, FastAPI cancels the surrounding task,
which cancels the generator, which cancels the underlying LangGraph
run cleanly (verified by langgraph's built-in
`asyncio.CancelledError` handling). Our existing httpx-based path in
`AgenticResearchService._call_ollama_stream` does the same thing —
the M4 rewrite preserves the property.

**Token streaming caveat:** `on_chat_model_stream` only fires when
the underlying LLM is streaming. `ChatOllama` streams by default
(`disable_streaming=False`), so we get token events for free. If a
future provider doesn't stream, M4 falls back to a single
`on_chat_model_end` event with the full text — caller code should
treat the absence of streamed tokens as graceful degradation.

---

## 6. Subagent Dispatch (the M3 hook)

deepagents has **two** subagent flavors:

1. **`SubAgent`** (declarative, sync) — exposed via the built-in
   `task(subagent_name, prompt)` tool. The orchestrator decides when
   to dispatch.
2. **`AsyncSubAgent`** (LangGraph remote) — runs against a remote
   Agent Protocol server. Out of scope for M2.

### What M3 needs

M3's `SubagentPool` caps `max_concurrent = 4` per-article reasoning
tasks. The cleanest deepagents-native path:

```python
from deepagents import SubAgent, create_deep_agent

per_article_subagent = SubAgent(
    name="per-article-analyzer",
    description=(
        "Analyzes a single article in isolation. Use when you need a "
        "focused summary, entity list, or focus-question answer for "
        "ONE article. Inputs: article_id, focus_question (optional)."
    ),
    system_prompt=(
        "You are analyzing exactly one article. You have access to "
        "summarize_article and extract_entities tools. Answer ONLY "
        "from the provided article body — do not invent facts."
    ),
    tools=[summarize_article, extract_entities],   # M2's tools
    # model=...                                    # optional override
)

agent = create_deep_agent(
    model=llm,
    tools=[search_articles, query_knowledge_graph],
    subagents=[per_article_subagent],
    system_prompt="...",
)
```

Then the main agent calls
`task(subagent_name="per-article-analyzer", prompt="article_id=42, ...")`
and deepagents spins up an isolated subagent context.

**But** — deepagents' built-in `SubAgentMiddleware` does NOT
implement a concurrency cap. M3 has two options:

- **Option A: wrap the dispatcher.** Subclass `SubAgentMiddleware`,
  override `_dispatch_subagent`, gate it on
  `asyncio.Semaphore(max_concurrent)`. Pass the custom middleware via
  `middleware=[SubagentPoolMiddleware(...)]`.
- **Option B: roll our own pool outside deepagents.** Skip declarative
  subagents entirely; expose a single `analyze_article` tool that the
  orchestrator calls with a list of article IDs. Inside that tool,
  dispatch N parallel async tasks gated by `asyncio.Semaphore(4)`.
  Each task runs an inner `create_deep_agent(...)` build with one
  article in its prompt.

**Recommendation: Option B.** Reasons:

1. The orchestrator's prompt-discipline contract (M4 acceptance:
   "orchestrator prompt contains article IDs + summaries but NEVER
   raw body text") is easier to enforce when our code controls the
   per-article prompts.
2. The semaphore lives in our code, not in middleware we'd have to
   reach into.
3. We get explicit control over which `subagent: start/done/error`
   events fire on the SSE stream — no need to translate
   deepagents-internal subagent events.

Option B is essentially the "custom asyncio.Semaphore + dataclass
skill registry" path the original M1 issue described as the NO-GO
fallback. With deepagents adopted for the *outer* loop, the *inner*
per-article reasoning still benefits from being a hand-rolled pool.
The mission can use both: deepagents for orchestration,
`SubagentPool` for fan-out.

The M3 worker should pick this path unless a clean middleware
override appears in deepagents 0.6+.

---

## 7. Context Filtering Hooks (M4 keeps the orchestrator prompt bounded)

The M4 acceptance criterion "orchestrator prompt contains article IDs +
summaries but NEVER raw body text" is enforced by **what the tools
return**, not by deepagents middleware.

deepagents' built-in `SummarizationMiddleware` rewrites the agent's
message history when it grows too long, but it operates AFTER tool
returns are already in the context. The cleaner enforcement is at
the tool-return boundary:

```python
@tool
def search_articles(query: str, limit: int = 3) -> str:
    """..."""
    raw_hits = ...  # full search results with body text
    # ENFORCE: the orchestrator must never see raw body text.
    # Strip body, keep id/title/url/source/summary only.
    safe = [
        {
            "id": h["id"],
            "title": h["title"],
            "url": h["url"],
            "source": h["source"],
            "summary": (h.get("summary") or "")[:300],  # capped
            "score": h["score"],
        }
        for h in raw_hits
    ]
    return json.dumps({"results": safe})
```

The per-article subagent (M3) is the only context that sees the
`articles.body` field — and its prompt is per-dispatch, so it can
never leak back into the orchestrator's history.

**Optional: `SummarizationMiddleware` for safety net.** If we want a
backstop, deepagents lets you tune it:

```python
from langchain.agents.middleware import SummarizationMiddleware

middleware = [
    SummarizationMiddleware(
        max_tokens_before_summary=8000,  # cap orchestrator context
        keep_messages=4,                 # always keep last 4
    ),
]
agent = create_deep_agent(..., middleware=middleware)
```

The M4 worker decides whether to keep this on. The contract test
("orchestrator prompt never contains raw body text") is satisfied by
tool-return stripping alone; summarization middleware is belt-and-
braces.

---

## 8. Bridge to our existing async-generator pattern (full M4 reference)

For convenience, here is the **complete** sketch of the M4
`AgenticResearchService.run` rewrite, combining sections 5 and 6:

```python
from typing import AsyncGenerator, Any, Dict
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from src.core.config import get_settings

class AgenticResearchService:
    def __init__(self, ...):
        self._agent = None  # built lazily

    async def _build_agent(self):
        settings = get_settings()
        llm = ChatOllama(
            model=settings.ollama_model or "gpt-oss:20b",
            base_url=settings.ollama_host or "http://localhost:11434",
            client_kwargs={"timeout": settings.ollama_timeout or 60},
            async_client_kwargs={"timeout": settings.ollama_timeout or 60},
            temperature=0.2,
        )
        return create_deep_agent(
            model=llm,
            tools=[search_articles, summarize_article, extract_entities,
                   query_knowledge_graph],
            system_prompt=ORCHESTRATOR_PROMPT,
        )

    async def run(self, question: str) -> AsyncGenerator[Dict[str, Any], None]:
        if not (question or "").strip():
            yield {"type": "error", "data": "Question cannot be empty"}
            return

        if self._agent is None:
            self._agent = await self._build_agent()

        yield {"type": "phase", "data": "Planning"}

        final_text = ""
        try:
            async for ev in self._agent.astream_events(
                {"messages": [{"role": "user", "content": question}]},
                config={"recursion_limit": 32},
                version="v2",
            ):
                kind = ev.get("event")
                if kind == "on_tool_start":
                    yield {
                        "type": "subagent",
                        "data": "start",
                        "tool": ev.get("name"),
                        "args": ev.get("data", {}).get("input"),
                    }
                elif kind == "on_tool_end":
                    output = ev.get("data", {}).get("output")
                    content = getattr(output, "content", "") if output else ""
                    yield {
                        "type": "subagent",
                        "data": "done",
                        "tool": ev.get("name"),
                        "result_size": len(content) if isinstance(content, str) else 0,
                    }
                elif kind == "on_chat_model_stream":
                    chunk = ev.get("data", {}).get("chunk")
                    text = getattr(chunk, "content", "") if chunk else ""
                    if isinstance(text, str) and text:
                        yield {"type": "token", "data": text}
                elif kind == "on_chat_model_end":
                    output = ev.get("data", {}).get("output")
                    content = getattr(output, "content", None) if output else None
                    if isinstance(content, str) and content.strip():
                        final_text = content
        except Exception as exc:  # noqa: BLE001
            yield {"type": "error", "data": f"Agent run failed: {exc}"}
            return

        yield {"type": "phase", "data": "done", "report": final_text}
```

**Citation guard rail:** the M1 service's
`_ensure_sources_section` post-processor still runs in M4 — wrap
`final_text` through it before yielding the terminal event. The
deepagents agent does not enforce `[N]` citations on its own.

---

## 9. Compatibility checks (the original M1 contract)

The issue ticket asked for ≥3 specific compatibility checks. Here
they are, with concrete evidence:

1. **deepagents installs cleanly on Python 3.13.** Verified via
   `pip install deepagents==0.5.7 langchain-ollama>=1.1.0` against
   `C:\Users\Tri\AppData\Local\Programs\Python\Python313\python.exe`.
   No build steps, no missing wheels.
2. **`gpt-oss:20b` supports Ollama's tool-calling protocol.**
   Verified via direct `POST /api/chat` with a `tools=[...]` payload —
   the model returns structured `tool_calls` entries with valid JSON
   arguments. Round-trip latency: ~1s for a calculator probe.
3. **`agent.astream_events(version="v2")` is a vanilla async
   generator.** It composes with our existing FastAPI SSE route
   pattern (`AgenticResearchService.run` is already an
   `AsyncGenerator[Dict[str, Any], None]`). Cancellation propagates
   correctly when the SSE client disconnects.
4. **The deepagents install does not break existing imports.** The
   17 contract tests still collect (`pytest --collect-only`); the
   backend `/health` endpoint still returns 200 after a restart.
5. **Tool registration is one decorator deep.** `@tool` from
   `langchain_core.tools` infers a JSON schema from the function
   signature. No bespoke registration framework to learn.

**Verdict: GO.** Mission 2 proceeds with deepagents for the outer
orchestration loop and a hand-rolled `SubagentPool` (option B in
section 6) for the per-article fan-out.

---

## 10. Known gotchas (read this before starting M2-M6)

- **Default tool stack is fat.** `create_deep_agent` adds 8+ tools
  the user can't see. M4 will need to either (a) trim the stack via
  `HarnessProfile` config, or (b) trust the system prompt to keep
  the model away from them. M1 spike used (b) — works for
  `gpt-oss:20b` but is not airtight.
- **The default subagent middleware adds a `task` tool.** Even with
  `subagents=[]`, deepagents adds a default `general-purpose`
  subagent and the `task` tool. Disable via
  `general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)`
  on a registered `HarnessProfile` (see the SDK docstring on
  `create_deep_agent`).
- **`astream_events` event names are LangChain v2.** They are stable
  but verbose — expect ~30-50 events per agent turn. Filter
  aggressively in the SSE bridge or you'll flood the frontend.
- **Sync-tool wrapping needs care inside a running loop.** The
  spike's `asyncio.run(_run())` works in standalone scripts but
  raises inside FastAPI request handlers (which are already in a
  loop). M2 should prefer `async def` tool bodies; if a sync wrapper
  is unavoidable, use `asyncio.get_running_loop().run_until_complete`
  is NOT safe — use `await loop.run_in_executor(None, blocking_fn)`
  instead.
- **`ChatOllama` reads `OLLAMA_HOST` env var if `base_url` is not
  passed.** Always pass `base_url` explicitly to avoid env-var
  drift between dev and prod.
- **No retry-on-tool-error built in.** If a tool raises, the agent
  sees the exception text in the message history and decides what
  to do. M3's "best-effort failure: skill_fn raise emits
  `subagent: error` event; dispatch returns None instead of
  raising" contract has to be enforced inside the tool body — wrap
  the body in try/except and return a JSON error payload.

---

## 11. Files touched in M1

- `backend/requirements.txt` — added `deepagents==0.5.7` and
  `langchain-ollama>=1.1.0` (and a comment block explaining the M2
  context)
- `backend/scripts/spike_deepagents.py` — NEW. The hello-world
  agent. Run with the explicit Python 3.13 path; prints tool calls,
  final output, wall clock.
- `docs/notes/deepagents-api-surface.md` — NEW. This document.

No production code paths touched. `AgenticResearchService` is
untouched (M4's job).
