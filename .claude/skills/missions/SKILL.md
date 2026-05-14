---
name: missions
description: Multi-agent execution framework for long-running software goals (hours-to-days, not minutes). Combines delegation, creator-verifier, broadcast, and negotiation into a single orchestrator-worker-validator pattern. Use this skill whenever the user wants Claude to "let it run for hours", "run a mission", "kick off a mission", "ship feature X end-to-end", "build the whole thing while I sleep", or otherwise hand off a multi-milestone software goal that's too big for a single conversational turn. Tightly integrates with grill-me (planning), write-prd (scoping), write-issue (milestone decomposition), and test-app-e2e (validation). Use this skill instead of starting work directly when the user's request involves more than one milestone or feature.
---

# missions — long-running multi-agent execution

A "mission" is software work that's too big for one conversation but small
enough to define up front: ship a feature, complete a refactor, build an
MVP, migrate a service. You — the orchestrator — plan it, spawn worker
subagents to implement each milestone serially, spawn adversarial validator
subagents to confirm correctness, and produce a final report.

**Three-role architecture (read `references/three-role-architecture.md`):**

- **Orchestrator** (you, this Claude) — plans, delegates, verifies, never
  edits code directly during execution
- **Workers** (subagents) — fresh context per milestone, implement, commit
  via git, hand off via structured report
- **Validators** (subagents) — adversarial; have NEVER seen the worker's
  code; produce verdicts independently

**Validation is a contract written before code, not a check after it.**
The orchestrator writes assertions during planning that define correctness
in terms a worker can't game by misinterpreting requirements.

## When to use this

- Multi-milestone work the user wants to hand off completely
- Anything described as "let me run this for hours / overnight"
- A goal big enough to require planning + decomposition + verification
- After grill-me + write-prd, when the user is ready to actually build

## When NOT to use this

- Single-file edits or bug fixes (just do it)
- Open-ended "let's explore the codebase" — no goal to converge on
- Anything the user wants to be in the loop on every step (Missions is for
  hand-off, not pair-programming)

## The four phases

### Phase 1 — Scope (planning)

Do NOT start implementation. The whole point of Missions is that planning
quality determines run quality.

1. **Run `grill-me`** to produce `docs/designs/<slug>.md`. This is the
   source of truth for the mission's goal and constraints.

2. **If scope warrants it (3+ milestones), run `write-prd`** to produce
   `docs/prds/<slug>.md`. Smaller missions skip this.

3. **Decompose into milestones.** A milestone is one ticketable feature
   that can be delivered + validated independently. Aim for 3–8 milestones
   total. Each milestone gets `write-issue` → `docs/issues/<slug>-<n>.md`.

4. **Write the validation contract** for each milestone (template in
   `references/validation-contract-template.md`). This is the part most
   teams skip and most failures trace back to. The contract is:
   - Functional assertions (X command produces Y output)
   - Behavioural assertions (clicking Z navigates to W)
   - Negative assertions (this should NOT happen)
   - Performance assertions (p95 under N ms)
   - Test commands the validator will run

5. **Save the mission plan** to `docs/missions/<slug>.md` with:
   - Link to design context, PRD (if any), each issue
   - Ordered list of milestones with their validation contracts
   - Estimated worker count, expected duration, kill-switch criteria

### Phase 2 — Approve

Show the user:
- The mission plan (high level)
- The milestones in order
- Each milestone's validation contract (top 3 assertions, link to full)
- An estimated wall-clock and rough subagent budget

Ask for explicit approval. **Wait.** Don't start until you get a clear yes.
The user can:
- Approve → continue to Phase 3
- Modify → go back to Phase 1 step 3 to re-decompose
- Cancel → save the plan as a draft and stop

### Phase 3 — Execute (serial, with validators)

Process milestones **one at a time** (`references/serial-vs-parallel.md`
explains why). For each:

1. **Spawn a worker subagent** using the briefing in `briefings/worker.md`.
   The worker gets:
   - The milestone's issue file path
   - The validation contract
   - The current git HEAD
   - Hard constraint: must commit work before returning
   - Hand-off format requirements (`references/handoff-format.md`)

2. **Read the worker's hand-off report.** Verify it has the required fields.
   If the worker says it's done but didn't commit, treat it as a failure.

3. **Spawn the Scrutiny Validator** using `briefings/validator-scrutiny.md`.
   The validator:
   - Has NOT seen any of the worker's reasoning or report
   - Receives only: the milestone goal, the validation contract, the git
     diff
   - Runs tests, typecheck, lint
   - Spawns a code-review subagent for substantive changes
   - Returns a verdict: pass / fail-with-reasons

4. **Spawn the User-Testing Validator** using
   `briefings/validator-user-testing.md` *if* the milestone touches user-
   facing surface (UI, API contracts, CLI). The validator:
   - Receives only: the user-flow assertions from the validation contract
   - Drives the actual app (computer-use, Windows-MCP, browser MCP, or
     curl for API-only)
   - For projects with `test-app-e2e`: runs the relevant subset of that
     suite plus any milestone-specific checks
   - Returns verdict + any reproductions of failures

5. **Decide the next move:**
   - **Both validators pass** → mark milestone complete, advance
   - **Either fails** → spawn the worker again with the failure report as
     additional input. Cap retry attempts at 3. After 3 failures, stop and
     surface the issue to the user.

6. **Update mission state** in `docs/missions/<slug>.md` after each
   milestone — what's done, what's next, what was learned. This is the
   broadcast pattern: a single source of truth that anyone (or a future
   resumed mission) can read to know where things stand.

### Phase 4 — Report and encode

When all milestones pass (or when stopping early):

1. **Write a final mission report** to `docs/missions/<slug>-report.md`:
   - What was implemented (link each commit)
   - What was left undone (and why)
   - Issues discovered along the way
   - Validator verdicts per milestone
   - Total wall-clock, subagent count, retries

2. **Encode learnings (`references/continuous-learning.md`).** If any of:
   - A worker tripped over the same gotcha twice
   - A new procedure emerged that wasn't in the existing skills
   - A class of bug was caught by validators
   ...then add it to the relevant skill (`test-app-e2e/references/`,
   `CLAUDE.md`, or a new skill via `skill-creator`).

3. **Hand back to the user** with the mission report path and a 5-line
   summary in chat.

## How to spawn subagents

In Cowork, use the `Agent` tool:

- **Worker**: subagent_type `general-purpose`, prompt = the briefing in
  `briefings/worker.md` filled in with milestone-specific values
- **Scrutiny Validator**: subagent_type `general-purpose` (or `code-reviewer`
  if available), prompt = `briefings/validator-scrutiny.md` filled in
- **User-Testing Validator**: subagent_type `general-purpose`, prompt =
  `briefings/validator-user-testing.md` filled in

**Run validators in parallel** (single message with two Agent tool calls)
because they don't conflict. **Run workers in series** because they share
the codebase.

The "fresh context" property in the slides is enforced by the briefing:
each subagent gets only the milestone goal, the contract, and the git diff
or HEAD. Don't paste your own thoughts into worker briefings — that
contaminates the adversarial property.

## Style rules

- **Plan more than you think you need to.** A 30-minute plan that produces
  a clean validation contract beats a 2-minute plan that produces a 6-hour
  debug session.
- **Validators must not see the worker's reasoning.** If they do, they
  inherit the worker's blind spots. Brief them with the goal, not the
  approach.
- **Workers must commit before returning.** Without a commit, the next
  worker can't inherit the changes. A worker that says "done" without a
  commit is a worker that hallucinated done.
- **One milestone at a time.** Resist the urge to parallelise. The slides
  are right — for multi-day runs, correctness compounds and parallelism
  burns tokens on conflict.
- **Update mission state after every milestone.** The mission file is the
  broadcast — your only durable memory across the run.
- **Cap retries at 3.** After three worker failures on the same milestone,
  surface to the user. Don't burn budget on a stuck milestone.

## Anti-patterns

- Skipping `grill-me` because "the user already knows what they want"
- Writing milestone validation contracts after the worker is done
- Letting workers decide their own contracts (they will optimise for
  pass-ability, not correctness)
- Spawning the validator with "the worker said it implemented X — please
  verify" (this contaminates the validator)
- Using parallel workers on overlapping files
- Long-running missions with no kill-switch — always define rollback /
  stop conditions during planning

## Bundled files

### references/
Open these when you need depth on a concept:
- `three-role-architecture.md` — orchestrator/worker/validator roles
- `validation-contract-template.md` — how to write a milestone contract
- `handoff-format.md` — the structured worker report shape
- `serial-vs-parallel.md` — when each pattern beats the other
- `recovery-procedures.md` — what to do when a milestone fails 3x
- `continuous-learning.md` — how to encode learnings back into skills

### briefings/
Templates the orchestrator pastes into `Agent` tool calls. Don't summarise
these in chat — paste them directly:
- `worker.md` — for the implementer subagent
- `validator-scrutiny.md` — for the code-review / tests validator
- `validator-user-testing.md` — for the QA / app-driving validator

### examples/
- `example-mission.md` — a worked mission for adding APScheduler-driven
  ingestion to this very project
