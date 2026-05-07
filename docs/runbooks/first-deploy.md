# First-deploy runbook (multi-project VPS)

This is the one-page setup you run **once**, by hand, the first time you
provision a VPS for this project. After this is done, every push to `main`
ships automatically via `.github/workflows/deploy.yml`.

If you've already done all of this and just want to redeploy: push to
`main`, or trigger the `Deploy to VPS` workflow via `workflow_dispatch`.

---

## 1. VPS prerequisites

- **OS**: Ubuntu 22.04 LTS (or any modern Debian/Ubuntu).
- **RAM**: 4 GB minimum, 8 GB recommended (Ollama keeps a 1B model warm).
- **Disk**: 20 GB minimum.
- **Software**:
  - Docker Engine 24+ with the Compose v2 plugin (`docker compose ...`,
    not the legacy `docker-compose` binary).
  - Caddy v2.

```bash
# Docker (official quickstart)
curl -fsSL https://get.docker.com | sudo sh

# Caddy (Debian/Ubuntu)
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

## 2. Create the deploy user

The deploy user owns `/opt/news-aggregator` and is the SSH target for the
GitHub Actions workflow. Lock it down to key-only auth.

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG docker deploy
sudo mkdir -p /home/deploy/.ssh
sudo chown deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
```

Lock down SSH (`/etc/ssh/sshd_config`):

```
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
```

`sudo systemctl reload ssh`.

## 3. Generate the deploy SSH key

**On your local machine** (not the VPS):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/news-aggregator-deploy -N ""
```

Append the **public** key to the VPS:

```bash
ssh-copy-id -i ~/.ssh/news-aggregator-deploy.pub deploy@<VPS_IP>
# or, manually:
cat ~/.ssh/news-aggregator-deploy.pub | ssh root@<VPS_IP> \
  "tee -a /home/deploy/.ssh/authorized_keys && \
   chown deploy:deploy /home/deploy/.ssh/authorized_keys && \
   chmod 600 /home/deploy/.ssh/authorized_keys"
```

Add the **private** key to GitHub Secrets:

- Repo → Settings → Secrets and variables → Actions → New repository secret
- Name: `DEPLOY_SSH_KEY`, value: the entire `~/.ssh/news-aggregator-deploy` file
- Also add: `DEPLOY_HOST` (VPS IP or hostname), `DEPLOY_USER` (`deploy`),
  optionally `DEPLOY_PORT` (default 22), `DEPLOY_DOMAIN` (e.g.
  `news.example.com` — leave unset to skip live E2E).

## 4. Lay down `/opt/news-aggregator`

On the VPS, as the `deploy` user:

```bash
sudo mkdir -p /opt/news-aggregator
sudo chown deploy:deploy /opt/news-aggregator
cd /opt/news-aggregator

# Pull the compose file from the repo. Two options:
#   (a) Clone the repo and symlink the compose file (easiest to keep updated):
git clone https://github.com/ductringuyen0186/ai-tech-news-assistant.git repo
ln -s repo/docker-compose.prod.yml docker-compose.prod.yml

#   (b) Or just copy the file — the deploy workflow only needs
#       docker-compose.prod.yml present at /opt/news-aggregator/.
```

## 5. Place the env file at `/etc/news/.env`

The compose file reads from `/etc/news/.env`. Permissions matter — this
holds API keys and the GHCR token.

```bash
sudo mkdir -p /etc/news
sudo touch /etc/news/.env
sudo chown root:docker /etc/news/.env
sudo chmod 640 /etc/news/.env
sudo nano /etc/news/.env
```

Minimum contents:

```env
# Public origin used for CORS. Single value, no wildcards.
ALLOWED_ORIGINS=https://news.example.com

# LLM provider keys (whichever you use).
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# GHCR pull token. Generate at https://github.com/settings/tokens with
# `read:packages` scope only. Used by `docker login` below.
GHCR_TOKEN=ghp_...
GHCR_USER=ductringuyen0186

# Optional: pin which image tag the box pulls. Defaults to :main.
# BACKEND_IMAGE=ghcr.io/ductringuyen0186/ai-tech-news-assistant:main
```

## 6. Authenticate Docker to GHCR

Once, as the `deploy` user:

```bash
. /etc/news/.env
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
```

This persists credentials at `~/.docker/config.json` so subsequent
`docker compose pull` calls in the workflow work without re-authing.

## 7. Pull the Ollama model

The `ollama` container starts empty. The first `chat` request would fail
with "model not found", so pull the small one ahead of time:

```bash
cd /opt/news-aggregator
docker compose -f docker-compose.prod.yml up -d ollama
docker exec news-aggregator-ollama ollama pull llama3.2:1b
```

The model lives in the `ollama_models` named volume from then on; it
survives `docker compose down`.

## 8. Configure host-level Caddy

Open `/etc/caddy/Caddyfile`. If you have other projects on this VPS,
they'll already have site blocks here — keep them. Append the snippet
from `deployment/Caddyfile.example` (in this repo), then set the
`DOMAIN` env var so Caddy substitutes the real subdomain:

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# Tell Caddy what domain to use.
echo 'DOMAIN=news.example.com' | sudo tee /etc/default/caddy

# Validate before reloading; a bad config kills *all* hosted projects.
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Until DNS is set, you can verify the snippet with:

```bash
curl -H "Host: news.localhost" http://127.0.0.1/health
```

## 9. DNS

Create an A record for the subdomain pointing at the VPS public IP. Wait
for propagation (`dig +short news.example.com`), then:

```bash
curl -i https://news.example.com/health
# Expect: HTTP/2 200, JSON body with "status": "healthy"
```

Caddy auto-issues a Let's Encrypt cert on the first request. If that hangs
or fails, check `journalctl -u caddy -f` for ACME errors (most common
cause: port 80 is firewalled, or DNS hasn't propagated yet).

## 10. Smoke-test the deploy workflow

In the GitHub UI: **Actions → Deploy to VPS → Run workflow** (against
`main`). Watch the logs. Expected end-to-end time: under 5 minutes.

If the live-E2E job is red, it's currently configured as **blocking**
for the first runs. After 3 consecutive green deploys, flip the gate:

```yaml
# .github/workflows/deploy.yml, in the `e2e` job:
env:
  BLOCK_ON_E2E_FAILURE: "false"
```

…and the suite becomes alert-only.

---

## When something goes wrong

**`docker compose pull` fails with 401 from ghcr.io**
The `docker login` from step 6 expired or wasn't run. Re-run it. The
GHCR PAT itself can also expire — generate a new one at
`https://github.com/settings/tokens` (scope: `read:packages`).

**Caddy returns 502 for `news.<domain>`**
Backend container isn't up or isn't on `127.0.0.1:8000`.
`docker compose -f /opt/news-aggregator/docker-compose.prod.yml ps`
should show both `news-aggregator-backend` and `news-aggregator-ollama`
running. If backend is restarting, check `docker compose logs backend`.

**Ollama responds with "model not found"**
You skipped step 7. `docker exec news-aggregator-ollama ollama list`
to confirm; pull again if needed.

**E2E suite times out against live URL**
Often Ollama's first call after a long idle. The workflow uses
`--skip-pipeline`, so the slow `summarize` test is excluded; everything
else should answer in seconds. If `/health` is also slow, the box is
under-provisioned (check `docker stats`).

**Sibling project on the VPS broke after a deploy**
This shouldn't happen — the compose project name `news-aggregator`
isolates volumes, networks, and container names. If it does, check
that the sibling project also pins its compose project name and
isn't sharing a network.

**Need to roll back**
The `:sha-<commit>` tag is preserved on GHCR. SSH in and:
```bash
cd /opt/news-aggregator
export BACKEND_IMAGE=ghcr.io/ductringuyen0186/ai-tech-news-assistant:sha-<old-commit>
docker compose -f docker-compose.prod.yml up -d
```

**Need to wipe and start over**
```bash
cd /opt/news-aggregator
docker compose -f docker-compose.prod.yml down --volumes  # nukes news_db_data + ollama_models
```
Be careful: this deletes the SQLite DB and the cached model.
