---
name: test-app-e2e
description: Run a black-box end-to-end smoke test of the AI Tech News Assistant (backend, summarization pipeline, and optionally frontend) without reading any application source code, then automatically dispatch a fixer agent for every failing test. Use this skill whenever the user asks to "test the app", "run e2e tests", "smoke test", "verify everything works", "check if anything is broken", "run a regression test", or after any change to ingestion, summarization, routes, deployment configs, or the frontend's API config — even if they don't say "end-to-end" explicitly.
---

# AI Tech News Assistant — E2E Test + Auto-Fix

This skill runs a black-box smoke test against a running deployment of the
AI Tech News Assistant and, for every failure, dispatches a fixer agent to
investigate and patch the problem. It's the fastest way to answer "is the
app working right now?" without manually curling endpoints.

The whole point of black-box testing is to behave like a real user:
**don't read application source code while running tests**. The test runner
talks to the app over HTTP and inspects observable behaviour. Source code
gets read only by the fixer agents, *after* a test has flagged something.

## When to use this

- User asks for an E2E / smoke / regression / sanity test
- After substantive backend changes (routes, services, repositories, DB schema)
- After updating `frontend/src/config/api.ts` or any API contract
- After dependency upgrades or environment config changes
- Before/after a deploy

## When NOT to use this

- For unit-test-style verification of a single function (use pytest directly)
- When the user wants you to write *new* tests (this runs an existing battery)
- For pure UI/visual checks (the runner only confirms HTML loads, not layout)

## Workflow

### Step 1 — Make sure the system is up

The runner expects:

1. **Backend** running, by default at `http://127.0.0.1:8000` (start with
   `cd backend && python -m uvicorn src.main:app --port 8000`).
2. **Ollama** running with the configured model pulled (default `llama3.2:1b`).
   The runner checks this and reports it as a separate dependency, not as a
   backend bug.
3. **Frontend** (optional) running on `http://localhost:5173`. Pass
   `--skip-frontend` if you don't need to test it.

Ask the user before starting any of these yourself — they may already have
them up in other terminals, and double-starting will fail with port-in-use.

If anything's missing, suggest the exact command(s) to start it. Don't
silently spin things up in the background; this is the user's machine and
they should know what's running.

### Step 2 — Run the test battery

```bash
cd ai-tech-news-assistant
python .claude/skills/test-app-e2e/scripts/run_e2e.py --json --out /tmp/e2e_report.json
```

Useful flags:
- `--backend URL` — non-default backend host
- `--frontend URL` — non-default frontend host
- `--ollama-host URL` — non-default Ollama host
- `--skip-pipeline` — don't run the orchestrator round-trip (faster)
- `--skip-frontend` — don't probe the frontend
- `--json` — emit machine-readable JSON to stdout
- `--out PATH` — also write JSON to a file (recommended; the fixer agents
  need it)

The runner is stdlib-only — no extra `pip install` step.

### Step 3 — Read the report

The JSON has this shape:

```json
{
  "summary": {"total": 10, "passed": 8, "failed": 2},
  "results": [
    {
      "name": "pipeline_summarize_pending",
      "category": "pipeline",
      "passed": false,
      "severity": "high",
      "duration_ms": 142,
      "detail": "orchestrator reported 1 failure(s): [...]",
      "request": {"method": "POST", "url": "..."},
      "response": {"status": 200, "body": {...}},
      "suggested_fix_area": "backend-orchestrator"
    }
  ]
}
```

Sort failures by severity (`critical` > `high` > `medium` > `low`) and
look for cascades — e.g., if `backend_reachable` failed, every other test
also failed; fix the root cause, ignore the downstream noise.

### Step 4 — Dispatch a fixer agent for each unique failure

For each failing test (or each cluster of tests sharing the same root
cause), spawn a fixer subagent. **Auto-fix mode: the fixer makes the code
changes and re-runs the failing test before reporting back.** Human
sign-off only happens after the fix.

Use the `general-purpose` subagent (or `Plan` if the failure is large
enough to warrant planning first). Do not spawn one fixer per test if
multiple tests share a root cause — group them.

Brief the fixer with:

1. **What failed.** The full failure record from the JSON (name, detail,
   request, response, suggested_fix_area).
2. **The fix-area cheat sheet.** Tell it to read
   `.claude/skills/test-app-e2e/references/troubleshooting.md`, specifically
   the section matching `suggested_fix_area`, before touching code.
3. **The constraint.** Make the smallest change that turns the failing
   test green. No unrelated refactoring, no new features.
4. **The verification step.** It must re-run
   `python .claude/skills/test-app-e2e/scripts/run_e2e.py --json` and
   confirm the failing test now passes (and that no previously-passing test
   started failing) before declaring success.
5. **Report shape.** Ask for: what the root cause was, what file/lines
   changed, the before/after snippet, confirmation the test now passes.

Example fixer prompt:

> The E2E runner found a failure. Here's the full record:
>
> ```json
> { ...the failure object from /tmp/e2e_report.json... }
> ```
>
> First, read
> `.claude/skills/test-app-e2e/references/troubleshooting.md` and find the
> section for `suggested_fix_area = backend-orchestrator`. That's your
> starting briefing.
>
> Make the smallest change that flips this test green. Don't refactor
> unrelated code. After your edit, re-run
> `python .claude/skills/test-app-e2e/scripts/run_e2e.py --json --out /tmp/e2e_report.json`
> and confirm:
>   1. `pipeline_summarize_pending` now passes.
>   2. No previously-passing test newly fails.
>
> Report: root cause, file/lines changed, before/after, and the new test
> result for the failing test.

Spawn fixers in parallel for unrelated failures, in series for failures
that touch the same files (otherwise their edits collide).

### Step 5 — Re-run and report

After all fixer agents return:

1. Run the suite one more time yourself (don't trust each fixer's
   self-report blindly — they may have only re-run the single test they
   owned).
2. Tell the user: what was broken, what each fixer did, and the final
   pass/fail tally.
3. If any failures remain, decide whether to dispatch another fixer round
   or escalate to the user.

### Style notes

- Treat infrastructure failures (`backend-startup`, `ollama-setup`,
  `frontend-startup`) differently from app failures. The first usually
  means "the user hasn't started something" — confirm with them rather
  than auto-editing files. The second is fair game for auto-fix.
- Don't read source files while running the test battery itself. Reading
  source while diagnosing in a fixer agent is fine and expected.
- The runner's tests are intentionally light — they confirm the contract,
  not deep correctness. If a fixer needs to verify deep logic, it should
  add a focused unit test in `backend/tests/` rather than over-extending
  the smoke tests.

## Bundled files

- `scripts/run_e2e.py` — the test runner. stdlib-only Python; runs
  anywhere with Python 3.9+.
- `references/troubleshooting.md` — fixer agent briefings, organised by
  the `suggested_fix_area` tags the runner emits. Don't try to summarise
  this in chat — point each fixer at the specific section it needs.
