# ─────────────────────────────────────────────
# TrustMoss API — Production Dockerfile for Render & Cloud Platforms
# ─────────────────────────────────────────────

FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="TrustMoss API"
LABEL org.opencontainers.image.description="Real-Time Trust, Security & Reliability Gateway for AI Agents"

RUN addgroup --system trustmoss && adduser --system --ingroup trustmoss trustmoss

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=trustmoss:trustmoss . .

USER trustmoss

ENV PYTHONPATH="/app/apps/api:/app/services:/app"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "apps.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
