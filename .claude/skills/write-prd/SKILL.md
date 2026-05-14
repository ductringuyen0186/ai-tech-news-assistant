---
name: write-prd
description: Writes a product requirements document (PRD) by consuming the shared design context produced by the grill-me skill, then asking PRD-specific gap questions, then generating a structured markdown PRD saved to docs/prds/. Use this skill whenever the user says "write a PRD", "draft a product requirements doc", "spec this out", "let's write the requirements", or asks for any product-level requirements artefact. If a grill-me design context file does not yet exist for this work, this skill defers to grill-me first - it will refuse to fabricate context.
---

# write-prd — produce a PRD from a shared design context

A PRD covers the product-level "what and why" of a body of work that's bigger
than a single ticket: a feature with multiple components, a new surface, a
significant change to existing behaviour. It assumes a shared understanding
already exists, so this skill is deliberately a thin layer on top of
`grill-me` — it does not re-litigate design decisions.

The deliverable is a markdown file at `docs/prds/<slug>.md`.

## When to use this

- After `grill-me` has produced a design context file for the work
- The work is bigger than one ticket but smaller than a multi-quarter program
- The user uses words like "PRD", "spec", "product requirements", "requirements
  doc", or "let's write up what this feature is"

## When NOT to use this

- The user just wants a single ticket — use `write-issue` instead
- No `grill-me` context exists yet — run `grill-me` first
- The user wants an architecture / engineering decision record (ADR) rather
  than a product doc — those have a different shape and audience

## Workflow

### Step 1 — Locate the design context

Look for `docs/designs/<slug>.md`. The slug usually matches the topic the user
just discussed.

If none exists:

> "There's no design context file for this yet. Want me to run `grill-me`
> first so we're aligned, then come back to the PRD?"

Wait for the user's call. **Do not invent context.** If the user insists on
writing a PRD without grilling, ask them which existing doc to pull context
from, or ask the high-leverage questions inline before writing.

### Step 2 — Read the context file end-to-end

Even though it was generated recently, read it carefully. Note:

- Anything in **Open questions** — those need to be either resolved or
  flagged as risks in the PRD
- Anything terse or vague — those are signs to ask one or two more
  PRD-specific questions before writing

### Step 3 — Ask PRD-specific gap questions

These are the dimensions a PRD needs that grill-me may not have covered.
Ask only the ones that are missing. Don't ask all of them.

- **Owner** — who's the DRI for this? (engineering owner, PM owner)
- **Stakeholders** — who needs to sign off? Who needs to be in the loop?
- **Timeline** — desired ship date, milestones
- **Rollout strategy** — feature flag? gradual rollout? pilot users?
  full launch?
- **Metrics** — leading and lagging indicators we'll watch
- **Tracking** — where will progress live? (Linear, Asana, GitHub Projects)
- **Dependencies on other teams** — do we need API help, design help,
  legal review?

Use `AskUserQuestion` if available; otherwise inline questions in chat.
Cap the round at 3–4 questions.

### Step 4 — Write the PRD

Save to `docs/prds/<slug>.md`. Use this template exactly so the org gets
consistent PRDs over time:

```markdown
# PRD: <one-line title>

| Field          | Value                                               |
|----------------|-----------------------------------------------------|
| Status         | Draft / In review / Approved / Shipped / Deprecated |
| Author         | <name>                                              |
| Owner          | <DRI name + role>                                   |
| Stakeholders   | <comma-separated names + roles>                     |
| Created        | <ISO date>                                          |
| Last updated   | <ISO date>                                          |
| Target ship    | <date or quarter>                                   |
| Design context | [docs/designs/<slug>.md](../designs/<slug>.md)      |

## Summary
<2-3 sentences. What we're building, for whom, and the core value. Should be
readable on its own by an exec who won't read further.>

## Problem
<The pain we're addressing. Concrete enough that a reader can picture the
moment a user feels this pain. Pull from the design context's "Goal" and
"Why now" sections.>

## Goals & non-goals

### Goals
- <Outcome we're trying to produce>
- <Outcome we're trying to produce>

### Non-goals
- <Thing we're explicitly *not* doing in this round>
- <Thing we're explicitly *not* doing in this round>

## Users & use cases

### Primary user
<Who they are, what they're trying to do, and what they currently do
instead.>

### Use cases
1. <Concrete scenario with a name. "Sara opens the dashboard at 9am and..."
   walks through the moment of value.>
2. <Concrete scenario>
3. <Concrete scenario>

## Requirements

### Functional
- <The thing it must do>
- <The thing it must do>
- <The thing it must do>

### Non-functional
- **Performance**: <e.g. p95 < 500ms>
- **Reliability**: <e.g. 99.9% availability>
- **Security**: <e.g. data encrypted at rest, auth required>
- **Accessibility**: <e.g. WCAG 2.1 AA>
- **Compatibility**: <browsers, OS, screen sizes>

## Success metrics

### Leading indicators
<What we'll watch in the first week to know we're on track.>

### Lagging indicators
<The outcome metric, measured at 30/60/90 days.>

### Rollback criteria
<What would make us revert this. Be specific.>

## Rollout plan
1. <Phase 1: e.g. internal dogfood>
2. <Phase 2: e.g. 5% feature flag>
3. <Phase 3: e.g. 100% rollout>

## Dependencies
- **Internal**: <other teams whose work this depends on>
- **External**: <vendors, APIs, libraries>
- **Blockers / unblocks**: <what must land first; what unblocks downstream>

## Risks & mitigations
| Risk           | Likelihood | Impact | Mitigation                           |
|----------------|------------|--------|--------------------------------------|
| <risk>         | L/M/H      | L/M/H  | <how we handle it>                   |

## Open questions
<Questions that need answers before / during build. Include who owns each.>
- <Question>: owner = <name>
- <Question>: owner = <name>

## Out of scope (FAQ-style)
**Q: Will this also do X?**
A: No, X is explicitly out of scope for v1. See "Non-goals".

**Q: <Anticipated stakeholder question>**
A: <Answer>

## Appendix
- Source design context: `docs/designs/<slug>.md`
- Related PRDs / ADRs: <links>
- Conversation log excerpts (optional)
```

### Step 5 — Hand off

After writing the file:

> "PRD saved to `docs/prds/<slug>.md`. Status is **Draft**. Suggested next
> steps:
> - Send to `<stakeholders>` for review
> - Once accepted, run `write-issue` for each functional requirement to
>   break this into ticket-sized work
> - Update `Last updated` and `Status` as it moves through review"

## Style rules

- **Quote the design context, don't paraphrase wildly.** If the design says
  "AI-powered news aggregator", don't drift to "intelligent content platform"
  in the PRD. Consistency lets readers cross-reference.
- **Keep it readable to a non-engineer.** A PRD's audience includes PM,
  design, legal, and engineering. Don't bury intent under jargon.
- **Be honest about open questions.** Listing 3 unresolved questions is
  better than papering over them with confident-sounding placeholder text.
- **Don't pad.** If the "Risks" table has one row, leave it at one row. PRDs
  fail when they look comprehensive but say nothing.
- **Match length to scope.** A small feature PRD should fit in one screen.
  A platform shift might need 4 pages. Don't pad either direction.

## Bundled files

- `references/prd-template.md` — the template above as a standalone file
  for copy-paste convenience
- `examples/example-prd.md` — a worked example showing how the template
  fills in for a real (small) feature
