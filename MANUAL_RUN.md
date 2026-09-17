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

## Step 10 — Simulate Docker Integration Smoke Test (Task 7.2)

This mirrors exactly what `.github/workflows/docker-integration.yml` runs:

```bash
# 1. Build all backend service images (5 targets in parallel mentally — runs serially locally)
docker compose build --no-cache

# 2. Start all services
docker compose up -d

# 3. Wait for healthy status (poll every 5s)
docker compose ps

# 4. Smoke test each health endpoint
curl -sf http://localhost:8000/health | python3 -m json.tool   # Gateway
curl -sf http://localhost:8001/health | python3 -m json.tool   # Guardrails
curl -sf http://localhost:8002/health | python3 -m json.tool   # Moss
curl -sf http://localhost:8003/health | python3 -m json.tool   # Evaluation

# 5. Smoke test JWT auth endpoint (end-to-end pipeline check)
curl -sf -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id":"manual-smoke","client_secret":"secret123","role":"agent"}' \
  | python3 -m json.tool

# 6. Teardown
docker compose down -v --remove-orphans
```

**Expected results:**
- All 4 `/health` responses: `{"service": "<name>", "status": "ok", ...}`
- Auth endpoint: JSON containing `access_token` and `"role": "agent"`

---

## Step 11 — Trigger a Versioned Release (Task 7.3)

Releases are **automated** — just push a semver tag and GitHub Actions does the rest.

```bash
# 1. Make sure you are on main and it is clean
git checkout main
git pull origin main

# 2. Tag the release (bump version as appropriate)
git tag v1.0.0 -m "Release v1.0.0 — Production readiness: CI/CD, Secrets, Database"

# 3. Push the tag — this triggers release.yml automatically
git push origin v1.0.0
```

**What happens automatically:**
1. All 6 Docker images built and pushed to `ghcr.io/<owner>/trustmoss-*:v1.0.0`
2. Images also tagged `:1.0`, `:1`, and `:latest`
3. GitHub Release created with structured changelog (feat/fix/perf/security grouped)

**To create a rolling edge release (no tag needed):**
Any push to `main` automatically creates/updates a `edge` pre-release with current images tagged `sha-<short>`.

**Pull images after release:**
```bash
docker pull ghcr.io/bhola-dev58/trustmoss-gateway:latest
docker pull ghcr.io/bhola-dev58/trustmoss-web:latest
# (repeat for other services)
```

---

## Step 12 — Run Supply Chain Security Audit Locally (Task 7.4)

```bash
source apps/api/.venv/bin/activate

# Scan production dependencies for CVEs
pip-audit --requirement apps/api/requirements.txt --format json --output pip-audit-prod.json
cat pip-audit-prod.json | python3 -m json.tool

# Scan dev/test dependencies for CVEs
pip-audit --requirement apps/api/requirements-dev.txt --format json --output pip-audit-dev.json
cat pip-audit-dev.json | python3 -m json.tool

# Quick human-readable scan (no JSON)
pip-audit --requirement apps/api/requirements.txt
```

**Expected result:** `No known vulnerabilities found` for both reports.

> **Note:** Dependabot PRs will appear automatically in GitHub each Monday–Thursday based on `.github/dependabot.yml`. No manual action needed.

---

## Architecture Reference

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — 23-node system topology
- [`docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`](docs/REQUIREMENTS_TRACEABILITY_MATRIX.md) — FR/MAC/test traceability
- [`docs/PROMPT_CATALOG.md`](docs/PROMPT_CATALOG.md) — CRISPE prompt template registry
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — Core CI pipeline (pytest + ruff + bandit + pip-audit)
- [`.github/workflows/docker-integration.yml`](.github/workflows/docker-integration.yml) — Docker build + integration smoke test
- [`.github/workflows/release.yml`](.github/workflows/release.yml) — Automated release & GHCR push
- [`.github/workflows/dependency-review.yml`](.github/workflows/dependency-review.yml) — PR supply chain security gate
- [`.github/dependabot.yml`](.github/dependabot.yml) — Automated dependency update PRs
- [`.github/SECRETS_SETUP.md`](.github/SECRETS_SETUP.md) — GitHub secrets configuration guide

