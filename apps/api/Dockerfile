# ─────────────────────────────────────────────
# TrustMoss API — Production-ready Dockerfile
# Multi-stage build: keeps image slim (~180 MB)
# ─────────────────────────────────────────────

# ── Stage 1: dependency builder ──────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps required for some wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ───────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="TrustMoss API"
LABEL org.opencontainers.image.description="Real-Time Trust, Security & Reliability Gateway for AI Agents"
LABEL org.opencontainers.image.version="0.1.0"

# Non-root user for security
RUN addgroup --system trustmoss && adduser --system --ingroup trustmoss trustmoss

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=trustmoss:trustmoss . .

# Remove local venv if accidentally included
RUN rm -rf .venv __pycache__

USER trustmoss

# Expose FastAPI port
EXPOSE 8000

ENV PYTHONPATH="/app/apps/api:/app/services:/app"

# Health check — Docker will restart if /health fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with uvicorn from apps/api directory so local imports resolve
CMD ["sh", "-c", "if [ -d apps/api ]; then cd apps/api; fi && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info"]
