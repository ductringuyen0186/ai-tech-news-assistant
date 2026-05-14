# Production Deployment Plan

> **Executive summary.** The app is currently dev-only — SQLite on disk, local Ollama for LLM, no auth, no CDN. To get it live on the internet we need: PostgreSQL (or stay on SQLite for v1), a cloud LLM (Groq is cheapest), backend on Render / Fly / Railway, frontend on Vercel / Cloudflare Pages, a domain, and basic monitoring. Total monthly cost at **hobby scale** (you + a handful of beta users): **$15–25/month**. At **small scale** (100 daily active users, a few hundred research queries/day): **$40–80/month**. At **medium scale** (1,000 DAU): **$200–500/month**. The single biggest variable is LLM spend — everything else is small fixed costs.

## 0. Where we are today

Working on your Windows machine:

- **Backend** — FastAPI + SQLite (`backend/news.db`), Ollama running locally for the agent + summarization.
- **Frontend** — Vite dev server on `:3000`.
- **Scheduler** — APScheduler in-process; only the retention job is wired (the new daily-ingestion mission adds the second job).
- **Auth** — none. No user table. Saved-research is a single shared list.
- **Embeddings** — sentence-transformers running on CPU, populated for all 80 articles.
- **Monitoring** — log lines to stdout. No error tracking.

What this means: anyone with the IP could read your whole DB. Don't expose it to the public internet until the items below are in place.

## 1. Gap analysis

These are the things that have to change between "works on Tri's laptop" and "works on the public internet."

| Concern | Today | Needs for prod | Cost |
| --- | --- | --- | --- |
| **Database** | SQLite file (`news.db`) | PostgreSQL (Render/Supabase/Neon) | $0–7/mo |
| **LLM runtime** | Local Ollama (`gpt-oss:20b`, ~13 GB VRAM) | Cloud API (Groq llama-3.1, OpenAI 4o-mini, or Claude Haiku) | $1–50/mo |
| **Backend hosting** | `uvicorn` on localhost | Render web service / Fly / Railway | $0–7/mo |
| **Frontend hosting** | Vite dev server | Vercel / Netlify / Cloudflare Pages (static) | $0/mo |
| **Domain + TLS** | none | A real domain with HTTPS | $1/mo amortized |
| **Cron** | APScheduler in-process | GitHub Actions cron OR Render Cron Job | $0–1/mo |
| **CORS / hardening** | `CORS *` allowed | Restrict to your frontend origin | $0 |
| **Secrets management** | hardcoded / env vars in shell | Render/Vercel env vars (encrypted) | $0 |
| **Auth** | none | API token for admin endpoints; optional user auth for "Saved" | $0 (or Clerk free tier) |
| **Error tracking** | stdout logs | Sentry (free tier) | $0 |
| **Analytics** | none | Plausible / Umami / PostHog | $0–9/mo |
| **Object storage** | not used | (skip — no images stored) | $0 |
| **Email** | not used | Resend / Postmark for daily digest emails | $0–10/mo |
| **Rate limiting** | none | `slowapi` middleware OR Cloudflare | $0 |

## 2. Recommended stack (cheapest path to live)

This is the "I want it live this weekend for under $20/month" version.

### Backend
- **Render Web Service**, starter tier ($7/mo) — always-on FastAPI container. Free tier exists but spins down after 15 min idle, which kills SSE research runs.
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `DATABASE_URL`, `LLM_API_KEY`, `OLLAMA_HOST` (if hybrid), `ADMIN_TOKEN`, `CORS_ALLOW_ORIGINS=https://yourdomain.com`

### Database
- **Render PostgreSQL** ($7/mo for the starter 256 MB plan).
- Migrate from SQLite via `sqlite_to_pg.py` script (need to write — see §4).
- Alternative: **stay on SQLite** for v1 if you don't need multi-instance. SQLite file on a Render persistent disk works fine for <1k QPS. Drops the DB cost to $0.
- Best free tier: **Supabase** (500 MB, no expiry) or **Neon** (3 GB free, branch-based, autoscaling).

### LLM
- **Groq** — by far the cheapest and fastest at the agent-research scale. `llama-3.1-70b-versatile` is free up to 14,400 requests/day. `mixtral-8x7b` similar. Speed is 5-10x OpenAI on the same model class.
- For better synthesis quality, **Anthropic Claude Haiku 4.5** at $0.25/1M input + $1.25/1M output tokens. A typical research run is ~5k input + 1.5k output = ~$0.003 per run. At 50 runs/day → $0.15/day → $4.50/month.
- For embeddings, **stay on sentence-transformers** running on the backend's CPU. Embedding a new article is ~20ms; cost is zero. Cloud alternatives (OpenAI text-embedding-3-small) cost $0.02/1M tokens — also tiny but adds a dependency for no gain.

### Frontend
- **Cloudflare Pages** or **Vercel** — both free for hobby. CF Pages has unlimited bandwidth and 500 builds/month; Vercel has the better DX. Either works.
- Build command: `npm run build`
- Output: `frontend/build/`
- Set `VITE_API_BASE_URL=https://api.yourdomain.com` env var so the SPA hits the backend.

### Cron
- **GitHub Actions** scheduled workflow, free for public repos and 2000 min/month private. Hits `POST /api/admin/ingest` once a day. Already specced in `docs/missions/daily-ingestion.md` §M5.

### Domain
- Anywhere — Namecheap, Porkbun, Cloudflare. ~$12/year for a `.com`. Cloudflare DNS is free and gives you analytics.

### Monitoring
- **Sentry** free tier — 5k errors/month, unlimited users. Install the FastAPI SDK on backend, React SDK on frontend. Catches every uncaught exception with stack trace + user session replay.
- **Render's built-in metrics** for CPU/RAM/request count — included with the web service.

### Email (optional, for daily digest)
- **Resend** — 3,000 emails/month free. Send the daily digest at 06:00 UTC after ingestion completes. Optional v1.5.

## 3. Cost projections

### Hobby tier — you + handful of beta users
| Line item | Cost |
| --- | --- |
| Render Web Service (starter) | $7 |
| Render PostgreSQL (or stay SQLite) | $0–7 |
| LLM (Groq free tier) | $0 |
| Vercel/Cloudflare Pages | $0 |
| Domain (amortized) | $1 |
| Sentry free | $0 |
| GitHub Actions cron | $0 |
| **Total** | **$8–15/month** |

### Small scale — 100 DAU, ~200 research queries/day
| Line item | Cost |
| --- | --- |
| Render Web Service (standard, 2 GB RAM) | $25 |
| Render PostgreSQL (1 GB) | $20 |
| LLM (Claude Haiku, 200 runs/day) | $20 |
| Frontend hosting | $0 |
| Domain | $1 |
| Sentry team tier | $26 |
| **Total** | **~$92/month** |

### Medium scale — 1,000 DAU, ~2,000 research queries/day
| Line item | Cost |
| --- | --- |
| Render Web Service (pro, 4 GB) | $85 |
| Render PostgreSQL (4 GB) | $95 |
| LLM (Claude Haiku, 2,000 runs/day) | $200 |
| Sentry business | $80 |
| Plausible analytics | $9 |
| Resend email (digest list) | $20 |
| **Total** | **~$489/month** |

**Caveat: the LLM line scales linearly with usage.** If you switch synthesis from Haiku to Claude Sonnet 4.6 (better quality, 4x cost) the medium-scale number jumps to ~$1,000/month. If you stay on Groq's free tier (subject to rate limits), it stays near zero up to ~14k requests/day. The "right" model depends on whether you're charging users for results — see the monetization plan.

## 4. Migration work needed

This is the actual to-do to get from where we are to production.

### 4.1 SQLite → Postgres (~3 hrs, optional for v1)
- Write `backend/scripts/sqlite_to_pg.py` — dumps every table from `news.db` and re-inserts into a Postgres database. Reuse the existing models so the schema's identical.
- Switch `database_url` to `postgresql://...` via env var. SQLAlchemy already supports both.
- Test: run the full Playwright suite against a Render preview deploy.
- **Defer to v2 if you don't want to do this now.** SQLite on a Render persistent disk works up to ~100 concurrent users.

### 4.2 LLM swap-in (~2 hrs)
- `langchain-groq` and `langchain-anthropic` are already in the venv (got pulled by deepagents).
- Add a config flag `LLM_PROVIDER=ollama|groq|anthropic` in `src/core/config.py`.
- Switch the agent's model from `ChatOllama` to a factory that returns `ChatGroq` / `ChatAnthropic` based on the env var.
- Keep Ollama as the dev default; prod uses Groq.

### 4.3 CORS + auth hardening (~1 hr)
- Tighten `CORSMiddleware` to only allow your frontend origin.
- Lock the `/api/admin/ingest` endpoint behind the `X-Admin-Token` HMAC check (already specced in the ingestion mission §M3).
- Add a global `slowapi` rate limit: 60 req/min/IP on public endpoints, unlimited for admin token. Keeps random scrapers from melting your LLM bill.

### 4.4 Deploy scripts + Render dashboard config (~1 hr)
- Add `render.yaml` at repo root describing the web service + Postgres + env vars. Render reads it on connect-repo and provisions everything.
- Wire `frontend/vercel.json` (or CF Pages equivalent) for the SPA with a rewrite rule sending everything to `/index.html` (so `/research`, `/feed`, etc. work on direct hit).

### 4.5 Sentry SDK install (~30 min)
- Backend: `pip install sentry-sdk[fastapi]` + 4-line init.
- Frontend: `npm install @sentry/react` + 4-line init in `main.tsx`.
- Add `SENTRY_DSN` env vars to Render and Vercel.

### 4.6 Domain (~30 min, async)
- Buy a domain. Point CNAME to Render + Vercel.
- Add custom domain in both dashboards. SSL auto-provisions via Let's Encrypt.

**Total migration effort: ~8 hours of focused work.** Most of it is config and copy-paste; only the SQLite→PG migration is substantive, and that's optional for v1.

## 5. Suggested rollout sequence

1. **Week 1** — Keep SQLite. Deploy backend to Render starter + frontend to Vercel + domain. Use Groq free tier for LLM. Get the site live behind a "Coming soon" banner with a waitlist form. Total cost so far: $8/month.

2. **Week 2** — Add Sentry. Add rate limiting. Add admin token. Start the daily ingestion cron via GitHub Actions. Invite 10 beta users.

3. **Week 3-4** — Watch the LLM bill. Watch Sentry for production errors. Add Plausible if you want analytics. If saved-research becomes a feature people use, add Clerk for user accounts ($25/month for the first 10k MAU) so saves are per-user instead of shared.

4. **Month 2+** — When LLM spend or DB size starts hurting, migrate SQLite → Postgres and re-evaluate LLM provider. By this point you'll have real usage signal.

## 6. Things explicitly out of scope for v1

- **Multi-region deploy.** Single Render region (US-East) handles thousands of users.
- **CDN for static assets.** Vercel/CF Pages already do this for free.
- **Real-time websockets beyond SSE.** SSE works on Render starter. WebSocket sticky-session routing needs the pro tier.
- **Mobile app.** The web app is already responsive-ish; native is a separate v2 product.
- **Account-level data isolation.** Saved-research is currently a global table; if you want per-user privacy that's a schema change. Defer until you have paying users who care.
- **PII compliance (GDPR/CCPA).** You're collecting public articles, not user data. Add a privacy policy + cookie banner when you turn on analytics.

## 7. Risk inventory

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Ollama not viable in prod | High | Already mitigated — Groq/Claude swap-in is 2 hours |
| Render free tier spins down between requests | Medium | Use $7 starter tier instead |
| LLM bill blows up overnight (someone scrapes) | Medium | Rate limit + admin token + daily budget cap on Anthropic dashboard |
| SQLite write contention at scale | Low | Doesn't matter at hobby scale; migrate later |
| RSS source rate-limits / blocks | Medium | Already exists; ingestion logs failures per feed and continues |
| Daily ingestion job silently breaks | Medium | M4 of the ingestion mission adds health endpoint + webhook alert |
| First user signs up, finds zero recent articles | Medium | Run a manual ingestion before launching; daily cron keeps it fresh |

## 8. One-liner: should you do this?

If the goal is **a public portfolio piece you can link from your CV**, the hobby-tier deploy ($8–15/month) is absolutely worth it. Looks vastly more impressive than "here's a screenshot."

If the goal is **to find out whether anyone actually wants to pay**, deploy the hobby tier, launch on Hacker News, add a waitlist form, and see what happens. Total monthly burn while you wait: under $20.

If the goal is **to build a real business**, see the monetization plan — but the deployment side is genuinely cheap until you have hundreds of users. The marketing is the bottleneck, not the infrastructure.
