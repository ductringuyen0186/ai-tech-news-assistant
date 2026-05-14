# Monetization Plan

> **Executive summary.** TechPulse AI has three plausible revenue paths, ranked by realistic dollar potential: (1) **B2B research seats** for VC analysts, corp dev, and industry research desks — $50–200/seat/month, this is where actual money lives; (2) **prosumer SaaS tiers** — $0 free / $8 pro / $20 team, the obvious play, modest ceiling; (3) **API access + white-label** for other apps to embed the agentic research — $30 self-serve / $500+ enterprise. Plus three smaller revenue streams: newsletter sponsorship, custom-research one-offs, and affiliate links on the "read article" CTA (less ethical and tiny revenue — skip unless desperate). The single most important strategic question is **who's the target user.** Pricing for "developers who want to play with an LLM agent" maxes out at $15/month forever. Pricing for "venture partner at a $200M fund who needs to track 60 AI startups" maxes out at $500/seat/month. The product is the same; the positioning, sales motion, and pricing are completely different.

## 0. What you're actually selling

Three things, in order of perceived value:

1. **The agentic research loop.** "Ask a deep question, get a cited answer in 30 seconds." This is the only feature anyone is going to pay for. The News Feed, Digest, and Knowledge Graph are commodity — you can get them from Google News, Techmeme, Hacker News for free. The agent is the thing only you have.
2. **A curated corpus.** The fact that you pre-ingest TechCrunch / Verge / Wired / Ars / MIT TR / HN and keep it fresh means the agent has clean fuel. Random "free Perplexity" doesn't have your curation. This becomes a moat if you add more sources (Stratechery, The Information, Bloomberg Tech with API access).
3. **A persistent reader's terminal.** Saved reports, Knowledge Graph of entities, Daily Digest — these create a habit. The free user who saves 10 research reports has switching cost.

The pitch a buyer hears: *"It's like having a junior analyst who reads the entire tech press every morning and can answer 'what's happening with X' in 30 seconds with citations."*

## 1. Revenue path A — Prosumer SaaS (obvious, low ceiling)

The textbook play. Direct-to-consumer freemium SaaS.

### Tier structure

| Tier | Price | Limits | Target buyer |
| --- | --- | --- | --- |
| **Free** | $0 | 5 research runs/day, no save history, daily digest in-app only | Casual readers, evaluators |
| **Pro** | $8/mo | Unlimited research, save up to 100 reports, email digest, custom topic subscriptions | Engineers, founders, journalists |
| **Team** | $20/seat/mo (3-seat min) | Pro + shared saved-research library, team digest, comment on saves | Small startup teams, podcasters, content creators |

### Realistic conversion math

Take the most generous assumptions you'd believe: 1% free→paid conversion is normal for prosumer LLM tools, 5% is exceptional.

- 1,000 free signups → 10 Pro @ $8 = **$80/month**
- 10,000 free signups → 100 Pro + 5 Team accounts @ avg $40 = **$1,000/month**
- 100,000 free signups → 1,000 Pro + 50 Team @ avg $40 = **$10,000/month**

To get to 100k free signups in a year you need a viral loop, an HN front-page hit, OR ~$3-5 CAC paid acquisition. The agentic-research-with-citations angle is genuinely differentiated, but every AI tool says that. **Honest assessment: realistic ceiling on this path alone is $1k-3k MRR within a year of launch, growing slowly. Good side income, not life-changing.**

### What you'd need to add to ship
- **Auth** — Clerk free tier handles up to 10k MAU. ~2 hrs.
- **Stripe** — Stripe Checkout + customer portal. ~3 hrs. Set up Pro ($8) and Team ($20) products.
- **Usage gates** — middleware that checks the user's tier before letting them call `/api/research`. ~2 hrs.
- **Email digest** — Resend integration + a daily job that emails subscribed users their digest. ~3 hrs.
- **Total**: ~10 hours of work to start collecting credit cards.

## 2. Revenue path B — B2B research seats (highest realistic ceiling)

The play that almost nobody starts with but ends up being where the money is.

### Who actually has a budget for this

- **Junior VC analysts** — every venture fund has a sub-partner whose job is "stay on top of the AI/tech space." They currently use a $40/month Substack stack + 2 hours/day of skimming. Replace 80% of that with TechPulse and they save 4 hours/week.
- **Corporate strategy teams** — Fortune 500 strategy / corp dev departments. Same problem, bigger budget. They already pay CB Insights $30k+/year for similar intel.
- **Industry analyst desks** — Forrester / Gartner / 451 analysts cover dozens of companies; the daily skim is meaningful labor.
- **Journalist research desks** — tech publications (Information, Insider, etc.) — but journalists are price-sensitive.
- **Investor relations + competitive intelligence** at AI startups themselves.

### Pricing

- **Individual seat**: $50/month/seat (annual: $500/year, 17% off).
- **Team seat (5+ seats)**: $40/month/seat.
- **Enterprise (20+ seats, custom features)**: $30/seat/month + setup fee.
- **Add-on: custom feed sources** (paywalled outlets, podcast transcripts, earnings calls): $100/source/month.

### Why these numbers work

CB Insights is ~$30k/year. PitchBook is ~$25k/year. They're the incumbents. A single TechPulse seat at $600/year is 50× cheaper. **You're not competing on the same axis** — those tools have deal-flow data; you have synthesized news intelligence. But the buyer's budget pool is the same one, and $600/year on a research tool gets approved without a meeting at any fund.

### Realistic math

- 10 paying seats at $50 = $500/month MRR. Achievable in 6 months with 20 cold-outreach LinkedIn DMs/week to VC analysts.
- 50 paying seats = $2,500/month. Plausible at 12 months with one good case study (e.g., "the BloombergGPT post that made the rounds in Sept came from a TechPulse query").
- 200 paying seats = $10,000/month MRR. Real business. Requires a small enterprise sales motion or one big team contract.

### What you'd need to add
- All of Path A's pieces (auth, Stripe, usage gates).
- **Bespoke source ingestion** — the buyer wants their internal newsletter ingested, their team's RSS feed of prior emails, etc. ~10 hrs to build a "bring your own feed" UI.
- **Team library** — shared saved-research per organization. ~4 hrs.
- **CSV / PDF export** of research reports. ~2 hrs (PDF via headless Chromium).
- **Slack integration** — `/techpulse <question>` slash command. ~6 hrs. Huge sales unlocker for teams.
- **An actual sales motion.** Cold outreach + 30-min demos + invoices. Founder-led for the first 50 seats; harder after that.

**This is the path with the highest realistic ceiling but the highest activation energy.** You're selling, not iterating product.

## 3. Revenue path C — API + white-label (developer audience)

Other developers want to embed agentic news research in their own app. Not many will pay, but the ones who do can pay a lot.

### Tier structure

- **Self-serve API**: $30/month for 1,000 research runs. $0.05/run after. Usage-based.
- **Embed widget**: free JS widget that embeds the research UI on any site. Co-branded ("Powered by TechPulse"). Pay $200/month to remove the brand.
- **White-label enterprise**: $500–2,000/month. Full removal of TechPulse branding, hosted on customer's subdomain (`research.theircompany.com`), custom source list.

### Who buys this

- Crypto/AI/fintech blogs that want to add "Ask our AI about today's news" to their site.
- Slack-bot SaaS companies that want a news-context tool in their feature set.
- Internal company portals that want a tech-news skill in their LLM chat.

### Realistic math

- 5 self-serve API customers + 2 white-labels = $30×5 + $1,000×2 = $2,150/month. Plausible at 12 months if you write a few "how I built this on the TechPulse API" blog posts.
- 20 self-serve + 5 white-labels = $600 + $5,000 = $5,600/month MRR. Requires aggressive developer marketing.

### What you'd need to add
- **API keys + rate-limited routes**. ~4 hrs.
- **A `/api/v1/research` endpoint** that's the API contract (separate from the frontend's `/api/research`). ~3 hrs.
- **An iframe-able widget**. ~6 hrs.
- **Stripe metered billing**. ~4 hrs.
- **Developer docs**. ~6 hrs of writing.

## 4. Smaller revenue streams

### Newsletter sponsorship
Once the daily digest has a couple thousand subscribers, sell a sponsored slot. Tech newsletters of similar size charge $100–500 per sponsor per send. With 5k subscribers and one sponsor per weekday, that's ~$2k/month at the low end.

Requires: meaningful subscriber count first (probably 6–12 months of organic growth).

### Custom research one-offs
"Pay $200 and we'll point the agent at your custom question and deliver a 10-page report tomorrow." Concierge tier above Pro/Team. A few orders/month is $1k extra MRR, and they convert into B2B seat sales.

Setup cost: zero — you literally just run the existing tool and email the result.

### Affiliate / outbound clicks
Honestly: skip. News-article affiliate is a race to the bottom, breaks trust, and the unit economics don't work at < 100k users.

## 5. Recommended path

**Stack A + B in that order.**

1. **Month 1–3**: Launch Path A. Free + Pro + Team tiers. Get paid traffic from product launch on HN, ProductHunt, the AI-tools newsletter circuit. Realistic: 1k–5k signups, $200–600 MRR. Whether or not this monetizes well is secondary — it gives you a public product to point at.

2. **Month 3–6**: While Path A grinds along, do **the B2B sales motion** in parallel. 5 cold LinkedIn DMs/week to junior VC associates. Offer them a free month, then $50/month. Once you've got 5–10 paying VCs, you have testimonials and the public story shifts from "yet another AI tool" to "what every junior VC associate uses to keep up."

3. **Month 6+**: B2B seats are growing 10–20%/month. Path A is steady-state. **Optionally add Path C** (API tier) if developer interest emerges from the public launch.

### Why this order

- Path A is **cheap to build** and gives you the marketing surface. You can't sell to VCs without a product to demo.
- Path B is **where the dollars actually are** but requires Path A as a public artifact.
- Path C is **easy to bolt on later** and doesn't compete with A or B.

## 6. Pricing positioning — the meta-decision

The single most consequential pricing decision is **where you anchor.**

- If you anchor at "I'm cheaper than ChatGPT Plus" → $20/month feels expensive. You're playing the consumer-AI-tool game and the ceiling is what Perplexity and Phind have.
- If you anchor at "I'm 50× cheaper than CB Insights" → $600/year/seat feels like a no-brainer. Different game, different ceiling.

**You can ONLY pick one anchor publicly.** The B2B Path B requires the product to feel like a "serious tool"; the consumer Path A requires it to feel like a "fun smart toy." The current "Broadsheet Terminal" aesthetic — Fraunces + IBM Plex + JetBrains Mono, mono dateline, teleprinter dispatch — actually anchors *toward the serious tool* end. That's a feature, not a bug, for B2B. For consumer it might read as "intimidating." Worth thinking about.

## 7. Things NOT to do (anti-pattern checklist)

- ❌ **Free forever with optional donations.** Doesn't work for LLM-cost tools. The cost-per-user makes free-forever a losing game.
- ❌ **Pay-per-query pricing for consumers.** Users hate the meter feeling. Unlimited-pro is psychologically necessary.
- ❌ **Sponsor the trending bar.** Erodes trust, low revenue, hard to sell because the bar is small.
- ❌ **Crypto / Web3 angle.** No.
- ❌ **"AI co-pilot for journalists."** Journalists are price-sensitive and the cohort is too small. VCs and analysts have the money.
- ❌ **Going freemium without rate limits.** A single user with `curl` + `for` loop costs you $50/month in LLM bills. Always rate-limit before charging.

## 8. The honest one-liner

**Build Path A, ship it, sell Path B.** Path A finances your domain + Render bill and gets you the public-facing product. Path B is where the real upside lives — 50 VC seats at $50/month is $30k/year of revenue from doing the same thing you already built. Don't try to chase both ICPs simultaneously; they need different messaging.

If you're not going to do the sales work for Path B, **just deploy Path A and treat it as a portfolio piece.** It's a legit one — a self-contained agentic-research-with-citations product is the kind of thing engineering managers click "schedule call" on when they see it on a resume. The monetization is just a bonus.
