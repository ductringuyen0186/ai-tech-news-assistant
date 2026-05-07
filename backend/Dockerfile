# Production Dockerfile for AI Tech News Assistant Backend
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# build-essential + python3-dev are needed to compile chroma-hnswlib from source
# on Python 3.13 (no pre-built wheels yet); removed after pip install to keep
# the image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies, then drop the C/C++ toolchain to slim the image.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
