---
name: write-issue
description: Writes a single GitHub-issue-sized ticket by consuming a grill-me design context and scoping it to one ticketable unit of work, then producing a structured markdown file at docs/issues/. Use this skill whenever the user says "write an issue", "create a ticket", "draft an issue", "let's spec this ticket", "open a Linear/Jira/GitHub issue for X", or wants any single-ticket-sized work artefact. Smaller scope than a PRD - one bug fix, one feature increment, one well-bounded refactor. If a grill-me design context exists, this skill uses it; if not, it asks the few questions needed to write a sharp issue without re-running the full grill-me workflow.
---

# write-issue — produce a ticketable issue spec

A good issue is the smallest unit of work that can be claimed by a single
person, completed in a few hours to a few days, and verified by an
acceptance-criteria checklist. This skill writes one — concise, scoped, with
clear definition of done.

The deliverable is a markdown file at `docs/issues/<slug>.md`. The slug is a
short kebab-case identifier (e.g. `fix-stale-summary-on-reingest`).

## When to use this

- A single bug fix
- A single feature increment ("add filter by source to the news list")
- A bounded refactor ("port `news_service.get_stats` off the legacy SQLite
  shim")
- A discrete chore ("add an APScheduler-backed daily ingest")
- After `write-prd` — break each functional requirement into a child issue

## When NOT to use this

- The work spans more than one obvious ticket — use `write-prd` to scope it,
  then come back here for individual children
- The user wants a full design doc — use `grill-me` for that
- The change is trivially small (one-line typo, version bump). Just do it.

## Workflow

### Step 1 — Locate or create context

Look for `docs/designs/<slug>.md` (or any other matching grill-me output).

- **If it exists**: read it. The "Affected surfaces", "Constraints", and
  "Failure modes" sections will fill in most of the issue.
- **If it doesn't exist**: do a *mini-grill*. Ask 2–4 sharp questions to
  cover the minimum a good issue needs (see Step 2). Don't run the full
  grill-me workflow — issue scope doesn't justify it. If the questions
  reveal the scope is bigger than an issue, stop and recommend `grill-me`
  + `write-prd`.

### Step 2 — Mini-grill questions (only if no design context)

The minimum to write a sharp issue:

1. **What outcome are you after?** (1 sentence — the "done" state)
2. **What does the current behaviour look like?** (for bugs: repro steps;
   for features: today's gap)
3. **Which file/area do you suspect?** (helps the assignee start)
4. **How will you know it's done?** (1–3 acceptance criteria)

Stop there. If the user starts answering with "well, we also need to think
about how it interacts with..." — that's a signal the scope is too big. Say:

> "Sounds like this is bigger than a single issue. Want me to switch to
> `grill-me` and we'll write a PRD instead?"

### Step 3 — Verify it's actually issue-sized

Before writing, check these heuristics:

- Estimated effort: <= ~3 days of one engineer's time
- Touches <= ~5 files (typically)
- Has a single clear "done" condition the assignee can self-verify
- Doesn't require coordination with other teams to land

If any of those fail, stop and recommend a PRD.

### Step 4 — Write the issue

Save to `docs/issues/<slug>.md`. Use this template exactly:

```markdown
# [<TYPE>] <imperative one-line title>

| Field          | Value                                            |
|----------------|--------------------------------------------------|
| Type           | Bug / Feature / Refactor / Chore / Docs / Test   |
| Priority       | P0 / P1 / P2 / P3                                |
| Estimate       | XS / S / M / L  (S = <1 day, M = ~2-3 days)      |
| Assignee       | <name or "unassigned">                           |
| Labels         | <comma-separated>                                |
| Linked PRD     | docs/prds/<slug>.md  (if applicable)             |
| Linked design  | docs/designs/<slug>.md  (if applicable)          |

## Context
<2-4 sentences. Why this work is being done. What's the current state and
the desired state. Pull liberally from the design context if it exists.>

## Description
<Concrete description of what to do. For a bug, include repro steps. For a
feature, describe the behaviour change. Avoid hand-wavy verbs like
"improve" or "enhance" - use concrete, observable verbs.>

### For bugs only
**Steps to reproduce:**
1. <step>
2. <step>
3. <step>

**Expected:** <what should happen>
**Actual:** <what happens today>

### For features only
**Today:** <current user-visible behaviour>
**After this change:** <new user-visible behaviour>

## Acceptance criteria
The issue is done when ALL of these are true:
- [ ] <Concrete, observable, self-verifiable criterion>
- [ ] <Concrete, observable, self-verifiable criterion>
- [ ] <Concrete, observable, self-verifiable criterion>

(Aim for 3-6 items. If you have 10, the issue is probably too big.)

## Implementation notes
<Optional - hints from the person who knows the area best. Files likely
involved, gotchas to watch for, related code patterns to mirror, tests to
update or add. Not a prescription - the assignee is allowed to deviate.>

Files likely involved:
- `<path/to/file.py>` — <why>
- `<path/to/other.tsx>` — <why>

Gotchas:
- <thing that bit us last time>
- <constraint that's not obvious from reading the code>

## Out of scope
<What this issue is *not* doing. Often as important as what it is doing.
Keeps PR review focused.>
- <thing>
- <thing>

## Verification
<How the assignee proves it works before requesting review.>
- <e.g. "Run `pytest tests/services/test_X.py`">
- <e.g. "Curl the endpoint and confirm response shape">
- <e.g. "Check the new behaviour in the local frontend">

## Risks
<Optional. One-line each. Skip if there are none worth flagging.>
- <e.g. "Touches the migration path - test against a fresh DB and an
  existing one">
```

### Step 5 — Hand off

After writing the file:

> "Issue saved to `docs/issues/<slug>.md`. Ready to drop into Linear /
> Jira / GitHub Issues. The acceptance criteria are the contract — if those
> pass, the work is done."

If the issue was generated as a child of a PRD, also update the PRD's "Open
questions" or "Functional requirements" section with a link back:

```markdown
- [docs/issues/<slug>.md](../issues/<slug>.md) — <one-line description>
```

## Style rules

- **Imperative title.** "Add source filter to news list" — not "We should
  add..." or "Source filtering". Verbs first.
- **Acceptance criteria are testable.** "Looks good" is not a criterion.
  "Returns HTTP 200 with `{success: true}` when given a valid query" is.
- **Pull from the design context.** If the context already specifies the
  affected surfaces, copy them into the issue. The assignee shouldn't
  have to read both.
- **Don't over-prescribe.** Implementation notes are hints, not rules. If
  the assignee finds a better approach, they should take it.
- **Skip empty sections.** If there are no risks worth listing, delete the
  Risks section. Empty headings are noise.
- **One-issue rule.** If you find yourself adding "and also" twice, the
  scope is wrong — split into two issues.

## Anti-patterns

- Putting "Q&A with stakeholders" inside an issue (that belongs in the PRD)
- Acceptance criteria that depend on subjective judgment ("the UI feels
  responsive")
- Using the issue body to argue for the work (the work was already approved
  in the PRD/design context)
- Bundling a bug fix and an unrelated chore "while we're in there" — make
  it two issues

## Bundled files

- `references/issue-template.md` — the template above as a standalone file
- `examples/example-issue.md` — a worked example for a real bug fix
