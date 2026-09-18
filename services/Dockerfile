# ─────────────────────────────────────────────
# TrustMoss Microservices — Production Dockerfile
# Multi-stage image supporting independent services:
# - gateway (8000)
# - guardrails (8001)
# - moss-service (8002)
# - evaluation-service (8003)
# - livekit-voice-agent (worker)
# ─────────────────────────────────────────────

FROM python:3.14-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Runtime Base ─────────────────────────────
FROM python:3.14-slim AS runtime-base

RUN addgroup --system trustmoss && adduser --system --ingroup trustmoss trustmoss
WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=trustmoss:trustmoss . .

# Ensure data directory exists and is owned by non-root trustmoss user
RUN mkdir -p /app/data && chown -R trustmoss:trustmoss /app

# Remove any stale bytecode and verify Python standard library secrets is unshadowed
RUN find . -type d -name __pycache__ -prune -exec rm -rf {} + \
 && find . -type f -name '*.pyc' -delete \
 && python -c "import secrets; assert hasattr(secrets, 'token_bytes'), 'secrets stdlib shadowed'"

ENV PYTHONPATH="/app/apps/api:/app/services:/app"
USER trustmoss

# ── Service Targets ──────────────────────────
FROM runtime-base AS gateway
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime-base AS guardrails
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["python", "-m", "uvicorn", "services.guardrails_service:app", "--host", "0.0.0.0", "--port", "8001"]

FROM runtime-base AS moss
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"
CMD ["python", "-m", "uvicorn", "services.moss_service:app", "--host", "0.0.0.0", "--port", "8002"]

FROM runtime-base AS evaluation
EXPOSE 8003
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')"
CMD ["python", "-m", "uvicorn", "services.evaluation_service:app", "--host", "0.0.0.0", "--port", "8003"]

FROM runtime-base AS voice-agent
CMD ["python", "apps/api/livekit_worker.py"]
