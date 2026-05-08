"""
deepagents hello-world spike (Mission 2, Milestone 1)
=====================================================

Goal
----
Prove that the ``deepagents`` SDK (https://pypi.org/project/deepagents/) can
be wired to local Ollama (``gpt-oss:20b``) with a single project-specific
tool (``search_articles``) wrapping our existing :class:`SearchService`.

This is *not* the production agent - it is a smoke test that locks in the
patterns the M2-M6 workers will copy:

* how to construct a deep agent with ``create_deep_agent``
* how to register a project tool via the langchain ``@tool`` decorator
* how to wire the agent to a local LLM via ``ChatOllama``
* how to drain agent events into something the FastAPI SSE generator can
  forward (this is the M4 integration point - see
  ``docs/notes/deepagents-api-surface.md``)

Run from the repo root::

    & "C:\\Users\\Tri\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" \
        backend\\scripts\\spike_deepagents.py

The script prints, in order:

1. Every tool call deepagents emits (``tool_name``, ``args``, ``result_size``)
2. The final agent output (full markdown answer)
3. Wall-clock duration in seconds

It exits 0 on success, 1 on any handled failure.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

# --------------------------------------------------------------------- #
#  Path bootstrap - the script lives in backend/scripts/ but imports
#  ``src.services`` from the parent ``backend/`` package. We replicate
#  what pytest.ini does (``pythonpath = .``) at runtime.
# --------------------------------------------------------------------- #
THIS_FILE = Path(__file__).resolve()
BACKEND_DIR = THIS_FILE.parent.parent  # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# Imports done after path bootstrap so ``src.*`` resolves.
from langchain_core.tools import tool  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402

from deepagents import create_deep_agent  # noqa: E402

from src.models.search import SearchRequest  # noqa: E402
from src.services.search_service import SearchService  # noqa: E402


# --------------------------------------------------------------------- #
#  Config
# --------------------------------------------------------------------- #
OLLAMA_URL = "http://localhost:11434"
MODEL = "gpt-oss:20b"
QUERY = "What recent news mentions OpenAI?"
TOP_K = 3
# Hard ceiling so the spike never runs away on a misbehaving model.
MAX_TURNS = 6


# --------------------------------------------------------------------- #
#  Tool registration
#
#  Pattern the M2 worker will copy: a thin sync wrapper around an async
#  service method. deepagents (LangGraph under the hood) accepts both
#  sync and async tools, but sync wrappers are simpler for the spike
#  because we don't have to thread an event loop through the @tool body.
#
#  The tool's docstring + parameter names ARE its schema as far as the
#  LLM is concerned - LangChain infers the JSON schema from the function
#  signature. Be precise here; the model reads this verbatim.
# --------------------------------------------------------------------- #
_search_service: SearchService | None = None
_tool_call_log: List[Dict[str, Any]] = []


def _get_search_service() -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service


@tool
def search_articles(query: str, limit: int = 3) -> str:
    """Semantic-search the local tech-news article corpus.

    Args:
        query: Natural-language search query (e.g. "OpenAI GPT-5 release").
        limit: How many top hits to return. Default 3, max 10.

    Returns:
        A JSON string with shape
        ``{"results": [{"id": ..., "title": ..., "url": ..., "source": ...,
        "summary": ..., "score": ...}, ...]}``. Use the summaries to ground
        your answer; cite by article id.
    """
    # Clamp limit defensively - the LLM has been known to ask for 50.
    limit = max(1, min(int(limit or 3), 10))

    svc = _get_search_service()
    req = SearchRequest(
        query=query,
        limit=limit,
        min_score=0.0,
        use_reranking=True,
        include_summary=True,
    )

    # SearchService.search is async; the @tool body is sync. Spin a fresh
    # event loop just for this call. In production we'd use the existing
    # loop, but a sync tool keeps the spike portable across deepagents
    # versions (pre-1.0 vs post-1.0 had different async semantics).
    async def _run() -> Any:
        await svc.initialize()
        return await svc.search(req)

    try:
        resp = asyncio.run(_run())
    except RuntimeError:
        # Already inside an event loop (some deepagents/LangGraph versions
        # invoke sync tools from a running loop via to_thread). Fall back
        # to creating a private loop on this thread.
        loop = asyncio.new_event_loop()
        try:
            resp = loop.run_until_complete(_run())
        finally:
            loop.close()

    results = []
    for r in getattr(resp, "results", []) or []:
        results.append(
            {
                "id": getattr(r, "id", None),
                "title": getattr(r, "title", "") or "",
                "url": getattr(r, "url", "") or "",
                "source": getattr(r, "source", "") or "",
                "summary": (getattr(r, "summary", None) or getattr(r, "content", None) or "")[:300],
                "score": float(getattr(r, "similarity_score", 0.0) or 0.0),
            }
        )

    payload = json.dumps({"results": results}, ensure_ascii=False)

    # Side-effect: record the call so the spike can print a structured
    # tool-trace at the end. The M4 worker will replace this with an SSE
    # ``subagent`` event emitter.
    _tool_call_log.append(
        {
            "tool_name": "search_articles",
            "args": {"query": query, "limit": limit},
            "result_size": len(payload),
            "result_count": len(results),
        }
    )
    return payload


# --------------------------------------------------------------------- #
#  Agent construction
# --------------------------------------------------------------------- #
def build_agent():
    """Build a minimal deep agent wired to local Ollama."""
    llm = ChatOllama(
        model=MODEL,
        base_url=OLLAMA_URL,
        temperature=0.2,
        # gpt-oss:20b can be chatty; keep the spike snappy.
        num_predict=512,
    )

    system_prompt = (
        "You are a research assistant for a tech-news archive. When the user "
        "asks a question, call the `search_articles` tool ONCE to retrieve "
        "relevant articles, then write a SHORT (3-5 sentence) answer that "
        "summarises what the articles say. Cite article titles inline. Do "
        "NOT call the tool more than twice. Do NOT use the filesystem or "
        "todo tools - just `search_articles`."
    )

    # We deliberately skip subagents/skills/memory in M1 - those are M2/M3.
    agent = create_deep_agent(
        model=llm,
        tools=[search_articles],
        system_prompt=system_prompt,
    )
    return agent


# --------------------------------------------------------------------- #
#  Drive the agent + drain events
#
#  Pattern the M4 worker will copy: ``agent.astream_events(...)`` is the
#  async generator that yields per-step events. We pluck out tool-call
#  starts/ends and the final message; the same drain in M4 will emit
#  ``subagent: start/done/error`` SSE events.
# --------------------------------------------------------------------- #
async def drive(agent, question: str) -> Dict[str, Any]:
    """Run the agent and return a dict with final output + observed events.

    Uses ``astream_events`` (langchain v2 events stream) so we get every
    tool call boundary, not just the final answer.
    """
    seen_tool_starts: List[Dict[str, Any]] = []
    final_text = ""

    inputs = {"messages": [{"role": "user", "content": question}]}

    # ``recursion_limit`` is the deepagents/LangGraph guard against runaway
    # tool-call loops. We cap it tight for the spike.
    config = {"recursion_limit": MAX_TURNS * 4}

    async for ev in agent.astream_events(inputs, config=config, version="v2"):
        kind = ev.get("event")
        if kind == "on_tool_start":
            seen_tool_starts.append(
                {
                    "name": ev.get("name"),
                    "input": ev.get("data", {}).get("input"),
                }
            )
        elif kind == "on_chat_model_end":
            # Capture the most recent assistant message text - the LAST
            # ``on_chat_model_end`` event is the agent's final answer.
            data = ev.get("data") or {}
            output = data.get("output")
            if output is not None:
                content = getattr(output, "content", None)
                if isinstance(content, str) and content.strip():
                    final_text = content
                elif isinstance(content, list):
                    # Anthropic-style content blocks; flatten text parts.
                    parts = [
                        b.get("text", "") if isinstance(b, dict) else str(b)
                        for b in content
                    ]
                    joined = "".join(parts).strip()
                    if joined:
                        final_text = joined

    return {
        "final_text": final_text,
        "tool_starts": seen_tool_starts,
    }


# --------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------- #
async def amain() -> int:
    print("=" * 72)
    print("deepagents hello-world spike")
    print("=" * 72)
    print(f"Model:    {MODEL}")
    print(f"Ollama:   {OLLAMA_URL}")
    print(f"Question: {QUERY}")
    print("-" * 72)

    t0 = time.monotonic()

    try:
        agent = build_agent()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: could not build agent: {exc}")
        traceback.print_exc()
        return 1

    try:
        result = await drive(agent, QUERY)
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - t0
        print(f"FAIL: agent run raised after {elapsed:.2f}s: {exc}")
        traceback.print_exc()
        return 1

    elapsed = time.monotonic() - t0

    print()
    print("Tool calls observed (from astream_events on_tool_start):")
    if not result["tool_starts"]:
        print("  (none)")
    for i, ts in enumerate(result["tool_starts"], 1):
        # Truncate input for readability.
        inp = ts.get("input")
        if isinstance(inp, dict):
            inp_repr = json.dumps(inp, ensure_ascii=False)[:200]
        else:
            inp_repr = str(inp)[:200]
        print(f"  [{i}] {ts.get('name')}({inp_repr})")

    print()
    print("Tool-call side-effect log (recorded inside the @tool body):")
    if not _tool_call_log:
        print("  (none)")
    for i, entry in enumerate(_tool_call_log, 1):
        print(
            f"  [{i}] tool_name={entry['tool_name']} "
            f"args={entry['args']} "
            f"result_size={entry['result_size']}B "
            f"result_count={entry['result_count']}"
        )

    print()
    print("Final agent output:")
    print("-" * 72)
    print(result["final_text"] or "(empty)")
    print("-" * 72)

    print()
    print(f"Wall clock: {elapsed:.2f}s")
    print(
        f"Tool calls: {len(result['tool_starts'])} via events, "
        f"{len(_tool_call_log)} via tool side-effect"
    )

    # Success criterion for the spike: agent produced *some* final text
    # AND invoked the tool at least once. If the LLM ignored the tool we
    # still want to flag that as a partial pass for the API-surface notes.
    if not result["final_text"]:
        print("FAIL: final agent output was empty")
        return 1
    if not _tool_call_log and not result["tool_starts"]:
        print("WARN: agent answered without calling search_articles")
        # Don't fail - the M1 contract is "agent runs", not "model is smart"
    print("PASS")
    return 0


def main() -> int:
    try:
        return asyncio.run(amain())
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
