# TrustMoss — Manual Run Guide

> **For developer use only.** Follow these steps to run, test, and verify the project manually on your local machine.

---

## Prerequisites

Ensure you have the following installed:

| Tool | Minimum Version | Check Command |
| :--- | :--- | :--- |
| Python | 3.11+ | `python --version` |
| Docker | 24+ | `docker --version` |
| Docker Compose | v2 plugin | `docker compose version` |
| Node.js | 18+ | `node --version` |
| Git | 2.40+ | `git --version` |

---

## Step 1 — Clone & Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd TrustMoss

# Copy environment template and fill in your keys
cp apps/api/.env.example apps/api/.env
```

Open `apps/api/.env` and fill in:

| Variable | Where to Get It |
| :--- | :--- |
| `GROQ_API_KEY` | https://console.groq.com |
| `MOSS_API_KEY` | Your Moss API console |
| `LIVEKIT_URL` | Your LiveKit Cloud project |
| `LIVEKIT_API_KEY` | Your LiveKit Cloud project |
| `LIVEKIT_API_SECRET` | Your LiveKit Cloud project |
| `ENCRYPTION_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

---

## Step 2 — Install Python Dependencies (Local Dev)

```bash
cd apps/api

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install production + dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Return to project root
cd ../..
```

---

## Step 3 — Run the Full Test Suite (121 Tests)

```bash
# From project root — activate venv first
source apps/api/.venv/bin/activate

# Run all 121 tests with coverage report
pytest apps/api/tests/ -v --tb=short --cov=apps/api --cov=services --cov-report=term-missing

# Run a specific test file
pytest apps/api/tests/test_auth_security.py -v

# Run tests by marker
pytest apps/api/tests/ -m security -v
pytest apps/api/tests/ -m unit -v
```

**Expected result:** `121 passed` with 0 failures.

---

## Step 4 — Run Linting (ruff)

```bash
# From project root (ruff.toml auto-discovered)
source apps/api/.venv/bin/activate
ruff check apps/api/ services/

# Auto-fix safe issues
ruff check apps/api/ services/ --fix
```

---

## Step 5 — Run Security Scan (bandit)

```bash
source apps/api/.venv/bin/activate

# Scan for MEDIUM and HIGH severity issues
bandit -r apps/api/ services/ -ll --exclude apps/api/.venv,apps/api/tests

# Generate JSON report
bandit -r apps/api/ services/ -ll -f json -o bandit-report.json
```

---

## Step 6 — Run with Docker Compose (Full Stack)

```bash
# Ensure apps/api/.env is filled (Step 1)

# Build all service images (first time takes ~3-5 min)
docker compose build

# Start all 6 services in background
docker compose up -d

# Check that all 6 services are healthy
docker compose ps

# Verify individual service health endpoints
curl http://localhost:8000/health   # Gateway
curl http://localhost:8001/health   # Guardrails
curl http://localhost:8002/health   # Moss
curl http://localhost:8003/health   # Evaluation
# Web UI: http://localhost:3000
```

---

## Step 7 — Verify Core API Endpoints

```bash
# 1. Obtain a JWT token
curl -s -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id": "dev-agent", "client_secret": "secret123", "role": "agent"}' \
  | python -m json.tool

# 2. Copy the "access_token" value and export it
export TOKEN="<paste_token_here>"

# 3. Run a query through the full pipeline
curl -s -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the refund policy?", "session_id": "manual-test-001"}' \
  | python -m json.tool

# 4. View HITL review queue
curl -s http://localhost:8003/hitl/queue | python -m json.tool

# 5. View prompt catalog
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/prompts/catalog \
  | python -m json.tool
```

---

## Step 8 — Stop All Services

```bash
# Graceful shutdown (preserves volumes)
docker compose down

# Full teardown including volumes
docker compose down -v
```

---

## Step 9 — CI Pipeline (Simulated Locally)

To simulate exactly what GitHub Actions runs:

```bash
# 1. Run tests with coverage (same as CI job 1)
source apps/api/.venv/bin/activate
pytest apps/api/tests/ -v --tb=short --cov=apps/api --cov=services \
  --cov-report=xml:coverage.xml --cov-fail-under=70 -p no:warnings

# 2. Ruff lint (same as CI job 2)
ruff check apps/api/ services/ --output-format=github \
  --select=E,F,W,I,N,UP,S --ignore=S101,S311,S603,S607,E501

# 3. Bandit SAST (same as CI job 3)
bandit -r apps/api/ services/ -ll \
  --exclude apps/api/.venv,apps/api/tests,apps/api/__pycache__ \
  -f json -o bandit-report.json
```

---

## Troubleshooting

| Problem | Fix |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'apps'` | Run pytest from **project root**, not from `apps/api/` |
| `ENCRYPTION_KEY not set` | Add a 64-char hex string to `apps/api/.env` |
| Docker port conflict on 8000 | Change `API_PORT` in root `.env.example` → copy to `.env` |
| `moss` package install fails | Ensure `pip install -r apps/api/requirements.txt` completes cleanly |
| `livekit-api` install fails | Requires Python 3.10+; check `python --version` |

---

## Architecture Reference

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 23-node system topology
- [`docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`](docs/REQUIREMENTS_TRACEABILITY_MATRIX.md) — FR/MAC/test traceability
- [`docs/PROMPT_CATALOG.md`](docs/PROMPT_CATALOG.md) — CRISPE prompt template registry
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — CI pipeline definition
