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

# Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# App source
COPY . .

# Non-root user + writable cache
RUN mkdir -p .hf_cache \
 && groupadd -r app && useradd --no-log-init -r -g app app \
 && chown -R app:app /app
USER app

# Start Gunicorn using Python config (reads PORT safely; no shell expansion)
CMD ["gunicorn", "-c", "gunicorn_conf.py", "run:app"]
