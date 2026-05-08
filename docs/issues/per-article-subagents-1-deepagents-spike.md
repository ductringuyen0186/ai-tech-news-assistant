# [Spike] Evaluate deepagents SDK against our async-generator pattern

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Spike                                                                  |
| Priority       | P0                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | backend, agent, deepagents, spike                                      |
| Linked PRD     | [docs/prds/per-article-subagents.md](../prds/per-article-subagents.md) — Milestone 1 |
| Linked design  | [docs/designs/per-article-subagents.md](../designs/per-article-subagents.md) |

## Context
Mission 2 picks deepagents (langchain) as the agent runtime, but the SDK has to fit our existing async-generator + SSE-streaming pattern. M1 is a 1.5-day spike that decides whether to adopt or fall back to a custom asyncio.Semaphore-based pool. Every downstream milestone depends on that decision.

## Description
**Today:** No deepagents in the project. M1's `AgenticResearchService` is a hand-rolled async generator.

**After this change:**
1. `deepagents` (or `langchain-deepagents`, whichever the canonical pip install resolves to) is installed and pinned in `backend/requirements.txt`
2. A scratch script `backend/scripts/spike_deepagents.py` instantiates a deepagents `Agent` with one tool/skill (`search_articles`), runs it against a hardcoded query against the live Ollama (`gpt-oss:20b`), and prints the agent's tool calls + final output
3. A doc note `docs/notes/deepagents-api-surface.md` captures the package's main API surface (Agent, Tool/Skill, Subagent, context filtering hooks) and contains an explicit GO / NO-GO recommendation with reasoning
4. The decision determines M2-M6's path: GO uses deepagents idioms; NO-GO falls back to custom asyncio.Semaphore + dataclass skill registry

## Acceptance criteria
- [ ] `deepagents` (or equivalent) appears in `backend/requirements.txt` with a specific version pin
- [ ] `backend/scripts/spike_deepagents.py` runs successfully against the live backend + Ollama and prints (a) the tool call deepagents made, (b) the final agent output, (c) the wall-clock duration
- [ ] `docs/notes/deepagents-api-surface.md` exists with sections: "Installation", "Core API", "Async generator integration", "Subagent dispatch", "Context-filtering hooks", "Verdict (GO/NO-GO)"
- [ ] The verdict cites at least 3 specific compatibility checks (e.g., "deepagents Agent.run is async — works with our generator pattern" or "deepagents requires LangChain LCEL chains, which conflict with our raw httpx Ollama calls")
- [ ] If GO: M2 worker can immediately start using the SDK. If NO-GO: the doc note describes the fallback architecture (custom SubagentPool + dataclass skills) in enough detail that M2 can proceed
- [ ] All 17 existing contract tests still pass

## Implementation notes
Files likely involved:
- `backend/requirements.txt` — add the dep
- `backend/scripts/spike_deepagents.py` — NEW, ~50-100 lines
- `docs/notes/deepagents-api-surface.md` — NEW

Gotchas:
- `gpt-oss:20b` is slow on CPU. Use a tiny query for the spike (e.g., "What is OpenAI?") to keep the script snappy
- deepagents may default to OpenAI; we need to wire it explicitly to local Ollama via langchain-ollama
- If the package install fails or has hard dependencies on Python features we don't have, that's a NO-GO
- Document any "this is doable but ugly" patterns in the doc note — the M2 worker will rely on it

## Out of scope
- Any of the 4 skills beyond `search_articles` (M2's job)
- The actual rewrite of `AgenticResearchService` (M4's job)
- The SubagentPool (M3's job)
- Any frontend changes

## Verification
- Run the spike script and observe a successful agent call with at least one tool invocation
- Read the doc note and confirm the verdict is unambiguous
- `pytest backend/tests/ --collect-only` still works (deepagents install didn't break anything)
- `python .claude/skills/test-app-e2e/scripts/run_e2e.py --skip-frontend` exits 0

## Risks
- deepagents may not exist as a clean pip package; the langchain ecosystem renames frequently. If the canonical install isn't obvious, document what was tried
- Ollama tool-calling may not work reliably with `gpt-oss:20b`; the spike must explicitly probe this
