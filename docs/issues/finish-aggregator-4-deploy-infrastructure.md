# [Feature] Stand up multi-project VPS deploy: Caddy + Compose + GitHub Actions push-to-main

| Field          | Value                                                |
|----------------|------------------------------------------------------|
| Type           | Feature                                              |
| Priority       | P0                                                   |
| Estimate       | L                                                    |
| Assignee       | unassigned                                           |
| Labels         | devops, ci-cd, deploy, infra                         |
| Linked PRD     | [docs/prds/finish-aggregator.md](../prds/finish-aggregator.md) — Milestone 4 |
| Linked design  | [docs/designs/finish-aggregator.md](../designs/finish-aggregator.md) |

## Context
The largest milestone. After this lands, every subsequent milestone ships
to a live URL via push-to-main. The whole shape is: VPS provisioned,
Caddy reverse-proxy fronts multiple projects on subdomains, our project
runs as a Docker Compose stack, GitHub Actions builds + pushes to GHCR
+ SSHes in to redeploy. Ollama runs as a sibling container (decision
made during this issue, see Open Questions).

## Description
**Today:** App runs on `localhost:8000` (backend) + `localhost:3000`
(frontend). No deploy pipeline exists. `deployment/render.yaml` is the
only deploy config and was for a different model.

**After this change:** A push to `main` on GitHub triggers a workflow
that runs tests, builds + pushes a Docker image to GHCR, then SSHes into
a VPS and brings the new image up. Caddy handles TLS + subdomain
routing. The site is reachable at `https://news.<domain>.tld` (or raw
IP first; domain is parked).

## Acceptance criteria

### Compose (production variant)
- [ ] `docker-compose.prod.yml` defines services: `backend`, `ollama`,
      `caddy` (caddy can be at the host level instead — pick one)
- [ ] `backend` exposes its port on `127.0.0.1` only (not `0.0.0.0`); Caddy
      is the only public-facing listener
- [ ] `ollama` runs `ollama/ollama:latest`, mounts a model volume, has
      `keep_alive=5m` configured via env
- [ ] Memory limits set: backend 512 MB, ollama 2 GB
- [ ] Persistent volumes: `news_db_data` for SQLite, `ollama_models` for
      pulled models
- [ ] Compose project name set to `news-aggregator` so it doesn't clash
      with sibling projects on the host

### Caddy (host-level, shared across all projects)
- [ ] `Caddyfile` (in repo at `deployment/Caddyfile.example` or similar)
      shows the snippet for this project's subdomain
- [ ] Snippet auto-issues TLS via Let's Encrypt for the project's
      subdomain
- [ ] CORS: backend already restricts origins via `ALLOWED_ORIGINS`; the
      production env sets it to the single live origin

### CI/CD (GitHub Actions)
- [ ] `.github/workflows/deploy.yml` triggers on push to `main` and
      `workflow_dispatch`
- [ ] Job sequence: checkout → run tests (must pass) → build image →
      push to GHCR with tags `:main` and `:<sha>` → SSH → deploy
- [ ] SSH step uses a deploy key stored in `secrets.DEPLOY_SSH_KEY`
- [ ] GHCR pull on the VPS uses a token in `/etc/news/.env` (or via
      `gh auth login` on the VPS, manual setup)
- [ ] Deploy command on the box: `cd /opt/news-aggregator && docker compose pull && docker compose up -d`
- [ ] Workflow posts a status comment on the commit with deploy result
- [ ] No-op change push deploys end-to-end in under 5 minutes
- [ ] Failed tests fail the workflow before any image push

### Co-tenancy
- [ ] Sibling projects on the VPS (real or simulated) keep running across
      a deploy — verified by leaving a long-running container running
      during a test deploy and checking it survives
- [ ] Per-container memory limits prevent one project from OOM'ing the host

### Live verification
- [ ] After first successful deploy, the E2E suite runs against the live
      URL: `python run_e2e.py --backend https://news.<domain>.tld
      --frontend https://news.<domain>.tld`
- [ ] First 3 deploys: E2E run is **blocking** (a red test fails the
      deploy). After that, switch to alert-only.

## Implementation notes
Files likely involved:
- `backend/Dockerfile` — already exists, audit; ensure non-root user,
  minimum needed pkgs, correct CMD
- `docker-compose.yml` (existing) → become or be superseded by `docker-compose.prod.yml`
- `deployment/Caddyfile.example` — NEW
- `.github/workflows/deploy.yml` — NEW
- `.github/workflows/ci.yml` — already exists; either reuse or extract
  shared steps
- `scripts/deploy.sh` — optional helper for the VPS-side command
- `docs/runbooks/first-deploy.md` — NEW; one-page setup guide for the
  VPS (install Docker, place env file, set up SSH key, configure Caddy
  symlink)

Gotchas:
- **Ollama model volume**: don't bake the 1.3 GB model into the image.
  Pull on first start: `docker exec news-ollama-1 ollama pull llama3.2:1b`,
  cached in the volume.
- **`news.db` persistence**: the volume must survive `docker compose
  down`. Use a named volume, not a bind-mount, unless you back up the
  bind path.
- **First-time VPS setup is manual**: install Docker, create `/opt/news-aggregator`,
  place env file, install + configure Caddy. Document this in
  `docs/runbooks/first-deploy.md` so it's reproducible.
- **GHCR auth**: the VPS needs a PAT with `read:packages` to `docker
  pull`. Generate once, place in `/etc/news/.env` as `GHCR_TOKEN`.
- **Domain not yet picked**: design works with raw IP. Caddy snippet
  shows `{$DOMAIN:news.localhost}` so we can default-render until DNS
  is set.

## Out of scope
- Provisioning the VPS itself (manual; "pick provider later")
- Domain registration (manual; out of scope for this run)
- Backups beyond VPS-snapshot (provider tooling handles it)
- Monitoring / alerting (skipped for v1)
- Multi-environment story (staging vs prod) — single env for now
- Removing the existing Render/Vercel-targeted configs (separate cleanup)

## Verification

### Local dry-run
```bash
docker compose -f docker-compose.prod.yml config        # YAML valid
docker compose -f docker-compose.prod.yml up -d         # local boots
curl http://localhost:<port>/health                     # backend up
docker compose -f docker-compose.prod.yml down
```

### CI dry-run (push to a branch first)
- Push a tiny commit to a feature branch
- The deploy workflow should NOT trigger (only `main` triggers it)
- Manually invoke `workflow_dispatch` to test the build+push without deploy

### Real deploy
```bash
# Set up the VPS once (per the runbook)
# Then:
git push origin main
# Wait < 5 min
curl https://news.<domain>.tld/health         # 200
python .claude/skills/test-app-e2e/scripts/run_e2e.py \
  --backend https://news.<domain>.tld \
  --frontend https://news.<domain>.tld
# all green
```

## Risks
- **Secrets leak in CI logs** → grep the workflow YAML for any `echo` of
  env, double-check `set +x` is implicit, never log full env dumps.
- **Deploy partially succeeds, leaves split-brain state** → the workflow
  should be a single SSH session; `set -e` so partial failure aborts.
- **Caddy + Let's Encrypt rate-limited during testing** → use the staging
  Let's Encrypt endpoint until the snippet is stable, then switch to prod.
- **Ollama OOM on first pull** → pull the 1B model first (1.3 GB), only
  add bigger ones if needed; warn if free RAM < 2 GB.
