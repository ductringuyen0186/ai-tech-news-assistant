# PRD: Daily AI summary digest email

| Field          | Value                                                  |
|----------------|--------------------------------------------------------|
| Status         | Draft                                                  |
| Author         | duc                                                    |
| Owner          | duc (eng + product, single-maintainer)                 |
| Stakeholders   | -                                                      |
| Created        | 2026-05-07                                             |
| Last updated   | 2026-05-07                                             |
| Target ship    | 2026-05-21                                             |
| Design context | [docs/designs/daily-digest-email.md](../designs/daily-digest-email.md) |

## Summary
Send a single daily email to the user at 8:00 local time containing the top
5 AI-summarised tech news stories from the previous 24 hours. The goal is to
make the existing aggregator "ambient" — usable without opening the app.

## Problem
The aggregator currently requires the user to actively open the dashboard to
get value. Most days that doesn't happen. The articles are summarised already;
the missing piece is delivering them where the user already is — email.

## Goals & non-goals

### Goals
- A user who never opens the web app still gets daily value from the system
- The email is concise enough to read in under 60 seconds
- Each story links back to its source AND to the in-app view

### Non-goals
- Multi-recipient / team digests — single-user only for now
- Configurable send time — fixed at 8:00 local in v1
- Per-topic filtering inside the digest — uses the same topic prefs as the app

## Users & use cases

### Primary user
The single user of the deployed app — opens email reflexively each morning,
opens the news app once or twice a week.

### Use cases
1. Morning catch-up. User opens email at 8:05am, scans 5 summaries, taps
   one that's interesting, lands on the in-app article view.
2. Quiet day. User sees the email contains nothing new (no fresh summaries
   in the last 24h), the email is suppressed entirely.

## Requirements

### Functional
- Cron-triggered job runs daily at 07:55 local
- Selects up to 5 articles where `summary_generated = true`,
  `published_at > now() - 24h`, ordered by relevance score
- Renders an HTML email with one card per story (title, source, summary,
  read-on-app link)
- Sends via SMTP / configured provider; logs delivery status
- If 0 eligible articles: skip send entirely (no empty email)

### Non-functional
- **Reliability**: retries 3 times with exponential backoff on send failure
- **Performance**: full job completes in < 30s
- **Security**: SMTP creds in env, never logged
- **Privacy**: no analytics pixel, no tracked links

## Success metrics

### Leading indicators
- Email send job completes successfully on day 1
- Email renders correctly in Gmail web + iOS Mail

### Lagging indicators
- 60% of days in a month, the user clicks at least one link in the digest

### Rollback criteria
- 3 consecutive days of send failures → disable the cron, alert the user

## Rollout plan
1. Day 1: dry-run mode — render the email, log to disk, don't send
2. Day 2-3: send to the maintainer's own inbox only
3. Day 4+: live

## Dependencies
- **Internal**: existing summarisation pipeline must be running daily
- **External**: SMTP provider (TBD: SendGrid free tier vs. own SMTP)
- **Blockers / unblocks**: blocks nothing; unblocks the "ambient" theme of
  the product

## Risks & mitigations
| Risk                                 | Likelihood | Impact | Mitigation                               |
|--------------------------------------|------------|--------|------------------------------------------|
| SMTP provider rate-limits us         | Low        | Low    | One email/day; well below any free tier  |
| Hallucinated summaries embarrass us  | Med        | Med    | Already filtered in the existing pipeline; rollback criteria above |

## Open questions
- Which SMTP provider? (owner: duc, decide before day 2 of rollout)
- HTML template — handcoded or library? (owner: duc, decide before day 1)

## Out of scope (FAQ-style)
**Q: Will the digest also include my upcoming calendar events?**
A: No. This is news-only in v1. Mixing surfaces makes the email harder to scan.

**Q: Can I get this on Slack instead?**
A: Not in v1. Email first; Slack channel is a future iteration.

## Appendix
- Design context: `docs/designs/daily-digest-email.md`
- Related: existing `/api/digest/` endpoint reuses the same selection logic
