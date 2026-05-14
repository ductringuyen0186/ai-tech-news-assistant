# Question Categories for grill-me

A taxonomy of questions to draw from while interrogating. Don't ask all of
them — ask the ones with the highest leverage on downstream decisions.

## Goal & motivation
- What does success look like a month after this ships?
- Who feels the pain that this fixes? Show me an example moment.
- If we did nothing, what's the worst-case six months from now?
- What's the goal *behind* the goal — what does this enable?

## Users / audience
- Who triggers this — a person, an automated system, both?
- How often does this happen per user / per day?
- What do they do today instead of this?
- Are they the same person every time, or a rotating pool?

## Scope (in / out)
- What's the smallest version that would still be valuable?
- What are we explicitly *not* doing here?
- Is this v1, or are we building toward something bigger?
- Does this replace something existing, or live alongside it?

## Constraints
- What can't change? (existing API, schema, deployment, auth model)
- What's the deadline, if any?
- What budget constraints (cost, infra, headcount)?
- Compliance / regulatory / security constraints?
- What's the team's current familiarity with the tech needed?

## Data
- Where does the input data come from? Format, freshness, volume?
- Where does the output go? Persisted, ephemeral, both?
- What's the source of truth? Can it disagree with itself?
- What about deletes / GDPR / right-to-erasure?

## Existing system
- What parts of the codebase does this touch?
- Are we extending an existing service or creating a new one?
- What contracts (API, schema, event) must we keep stable?
- What does the deploy story look like — same pipeline or new?

## Success criteria
- How will you know this worked, three months out?
- What's the leading indicator? The lagging one?
- Is there a metric we'll watch in production?
- What would cause us to *roll this back*?

## Failure modes & risk
- What's the worst thing that happens if this breaks?
- What user data is at risk?
- Can we put this behind a flag and disable it instantly?
- What's the blast radius of a bug?

## Alternatives & path-not-taken
- What did you consider before this?
- Why did you rule those out?
- Has the team tried something like this before?
- Is there an off-the-shelf option we'd be reinventing?

## Dependencies
- Does this need work from other teams to land?
- Is there an external service / vendor / library involved?
- What gets blocked if this slips?
- What blocks this if dependencies slip?

## Edge cases
- What happens when there's zero data? Massive data?
- What about concurrency / two users doing this at once?
- What about retries / duplicates / partial failure?
- What localisation / accessibility / device-class issues?

## Operations
- Who owns this once it ships?
- What's the on-call story?
- What logging / metrics / traces do we want from day one?
- Who will be the escalation point in week 2?

---

## How to use this list

1. Skim it during step 1 of the workflow.
2. Pick the **3–4 categories least obvious from the user's prompt**.
3. Within each category, pick the question that's most likely to surface a
   surprise. Boring questions get boring answers.
4. Don't ask every question in a category — pick the highest-leverage one.

You're not running through a checklist. You're hunting for the spots where
the user's mental model and your mental model would diverge if you started
building right now.
