# syntax=docker/dockerfile:1.6
#
# TechPulse AI backend image — multi-stage build for a slim runtime.
#
# Stage 1 (builder): installs all Python deps into a virtualenv at /opt/venv.
# Stage 2 (runtime): copies the venv + source, runs uvicorn.
#
# Sentence-transformers model (all-MiniLM-L6-v2, ~80MB) is pre-downloaded
# at image build time and baked into /opt/models so the first request
# doesn't pay a cold-start download tax.

# ─── builder ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create venv at /opt/venv so the runtime can copy it as a single dir
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python deps first (this layer is cached unless requirements.txt changes)
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Pre-download the sentence-transformer model so the runtime doesn't
# need to hit huggingface.co on first request.
RUN python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/opt/models'); print('model cached:', m)"

# ─── runtime ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SENTENCE_TRANSFORMERS_HOME=/opt/models \
    HF_HOME=/opt/models \
    # Default DB path inside the Fly volume mount.
    SQLITE_DATABASE_PATH=/data/news.db \
    DATABASE_URL=sqlite:////data/news.db

# Only the bare runtime libs needed; no build tooling in the final image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app

# Bring the prebuilt venv + model cache over from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/models /opt/models

# App source
WORKDIR /app
COPY . /app

# Ensure the Fly volume mount point exists before uvicorn boots.
# (Fly mounts `/data` at startup; this directory will be the persistent
# disk holding news.db, ingestion_runs, front_page_snapshots, etc.)
RUN mkdir -p /data && chown -R app:app /data /app /opt/models

USER app

# Healthcheck — Fly polls this to decide if the machine is alive.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

EXPOSE 8000

# Single worker is fine for hobby scale; uvicorn auto-reload OFF in prod.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
