FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf_cache

WORKDIR /app

# Build deps (removed after pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# Copy sources (big folders should be ignored by .dockerignore)
COPY . .

# Create user & writable dirs
RUN mkdir -p .hf_cache \
 && groupadd -r app && useradd --no-log-init -r -g app app \
 && chown -R app:app /app
USER app

# Healthcheck MUST use platform PORT
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD sh -c 'curl -sf "http://localhost:${PORT:-5000}/health" || exit 1'

# Bind to platform PORT (falls back to 5000 locally)
CMD ["sh","-c","gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 run:app"]
