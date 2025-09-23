# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (add curl + git for HF + healthcheck)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence transformer model to avoid download during runtime
# (works now with the pinned versions)
RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
SentenceTransformer('all-MiniLM-L6-v2')
print("Model cached")
PY

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data models/trained_models

# Set Python path to include src directory
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check (curl is now installed)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -sf http://localhost:5000/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "run:app"]
