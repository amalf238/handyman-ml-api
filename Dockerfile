FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf_cache

WORKDIR /app

# Build tools only for pip build time; removed after install
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove gcc g++ \
 && rm -rf /var/lib/apt/lists/*

# Copy only sources (big folders ignored by .dockerignore)
COPY . .

# Ensure writeable cache dirs
RUN mkdir -p data models/trained_models .hf_cache \
 && groupadd -r app && useradd --no-log-init -r -g app app \
 && chown -R app:app /app
USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -sf http://localhost:5000/health || exit 1

# Gunicorn entry
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "run:app"]