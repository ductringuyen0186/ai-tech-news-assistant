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

# Install Python deps first (this layer is cached unless requirements-prod.txt changes).
# Use the slim prod requirements file -- drops dev deps and packages our `src/`
# never imports (chromadb, langchain-community, langchain-groq, langchain-chroma,
# langchain-ollama, deepagents, 