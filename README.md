# TrustMoss

> **Real-Time Trust, Security & Reliability Gateway for AI Agents**  
> *YC Fall 2026 x Moss: Zero Latency Builder Sprint — Track: Agent Reliability, Security & Evaluation*

[![API Health](https://img.shields.io/badge/API-FastAPI%200.115-009688?logo=fastapi)](apps/api)
[![Frontend](https://img.shields.io/badge/UI-Vite%20%2B%20React-646CFF?logo=vite)](apps/web)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](docker-compose.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Overview

**TrustMoss** is an enterprise runtime trust and guardrail gateway that sits between an AI agent's retrieval step and response generation. Leveraging **Moss** as the low-latency contextual retrieval layer, TrustMoss evaluates every interaction in real-time, executing pre-generation and post-generation safety checks to issue a live **Trust Score** and prevent hallucinations before answers reach users.

---

## Architecture

Detailed architecture specifications and diagrams:
- **Architecture Spec:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Product Requirements Document (PRD):** [`docs/PRD.md`](docs/PRD.md)

### Key Subsystems

1. **Trust Gateway (FastAPI):** Rate limiting, authentication, payload sanitization, and request tracing.
2. **Inbound Guardrails:** Intercepts prompt injection attacks, jailbreaks, and scrubs user PII.
3. **Moss Retrieval Core (11ms avg):** Ultra-low-latency semantic + hybrid search for enterprise context.
4. **Pre-Generation Relevance Gate:** Filters out low-confidence chunks before passing context to the LLM.
5. **Agent Orchestrator:** Groq / Llama-3.1 context-grounded reasoning.
6. **Post-Generation Groundedness & PII Filter:** NLI and token overlap comparison against Moss context chunks.
7. **Tri-State Trust Aggregator & Circuit Breaker:**
   - [PASS] Relevance >= 0.7, Groundedness >= 0.7, Zero PII.
   - [WARN] Single borderline metric — served with disclaimer badge.
   - [FAIL] Severe hallucination or PII leak — Circuit Breaker trips to safe fallback.
8. **Human-in-the-Loop (HITL) & Knowledge Versioning:** Flagged outputs enter an audit queue; approved corrections are re-indexed into Moss.
9. **Observability & Telemetry:** OpenTelemetry tracing (Moss vs. Guardrails vs. LLM) + anomaly alerting.

---

## Quickstart — Docker (Recommended)

> One command. Any OS. Zero local dependencies (except Docker).

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — Windows / macOS  
  or [Docker Engine + Compose](https://docs.docker.com/engine/install/) — Linux

### Option A — Fully Automated Setup (All OSes)

**Windows** (run PowerShell as Administrator):
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**macOS / Linux** (requires [pwsh](https://github.com/PowerShell/PowerShell#get-powershell)):
```bash
pwsh setup.ps1
```

The script will:
1. Detect your OS and install Docker if missing
2. Create `.env` files from templates
3. Prompt for `GROQ_API_KEY` and `MOSS_PROJECT_KEY`
4. Build Docker images
5. Start all containers in detached mode
6. Run a health check and open the browser

### Option B — Manual Docker Setup

```bash
# 1. Copy env files
cp .env.example .env
cp apps/api/.env.example apps/api/.env

# 2. Edit apps/api/.env with your API keys:
#    GROQ_API_KEY=gsk_...
#    MOSS_PROJECT_KEY=...
#    MOSS_PROJECT_ID=...

# 3. Build and start
docker compose up --build

# Services will be available at:
# Dashboard  ->  http://localhost:3000
# API Docs   ->  http://localhost:8000/docs
# Health     ->  http://localhost:8000/health
```

### Common Docker Commands

| Command | Description |
|---|---|
| `docker compose up --build` | Build images and start all services |
| `docker compose up -d` | Start in detached (background) mode |
| `docker compose down` | Stop and remove containers |
| `docker compose logs -f api` | Stream API logs |
| `docker compose logs -f web` | Stream web logs |
| `docker compose ps` | Show container status |
| `docker compose restart api` | Restart the API container |

---

## Local Development (Without Docker)

> Use this when you want hot-reload during active development.

### Backend (FastAPI)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Edit with your keys
uvicorn main:app --reload --port 8000
```

### Frontend (Vite + React)

```bash
cd apps/web
npm install
npm run dev
# -> http://localhost:5173
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Full pipeline: Moss -> Guardrails -> LLM -> Trust Score |
| `GET` | `/history` | Session query history with latency breakdowns |
| `GET` | `/health` | Liveness check |
| `GET` | `/docs` | Interactive Swagger UI |

### Example Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the refund policy?", "top_k": 3}'
```

---

## Project Structure

```
TrustMoss/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py             # Core pipeline and endpoints
│   │   ├── moss_client.py      # Moss retrieval wrapper
│   │   ├── trust_score.py      # Tri-state aggregator
│   │   ├── tracer.py           # Per-hop latency tracer
│   │   ├── guardrails/         # Relevance, Groundedness, PII
│   │   ├── Dockerfile          # Multi-stage API image
│   │   └── requirements.txt
│   └── web/                    # React/Vite dashboard
│       ├── src/App.jsx         # Main dashboard UI
│       ├── Dockerfile          # Nginx-served build
│       └── nginx.conf          # SPA routing + API proxy
├── docs/                       # Architecture and PRD
├── docker-compose.yml          # Orchestrates all services
├── setup.ps1                   # Cross-OS automated setup
├── .env.example                # Root env template
└── README.md
```

---

## Environment Variables

### `apps/api/.env`

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | [Get from console.groq.com](https://console.groq.com/keys) |
| `GROQ_MODEL` | No | Default: `llama-3.1-8b-instant` |
| `MOSS_PROJECT_ID` | Yes | Your Moss project ID |
| `MOSS_PROJECT_KEY` | Yes | Your Moss project key |
| `MOSS_INDEX_NAME` | No | Default: `trustmoss-kb` |

### Root `.env` (Docker Compose ports)

| Variable | Default | Description |
|---|---|---|
| `API_PORT` | `8000` | Host port for the FastAPI backend |
| `WEB_PORT` | `3000` | Host port for the web dashboard |
| `VITE_API_URL` | `http://localhost:8000` | API URL called by the browser |

> If Moss or Groq keys are missing, the system automatically falls back to mock mode so you can still explore the UI and pipeline flow.

---

## Contributing

1. Fork the repo
2. Run `setup.ps1` (or `pwsh setup.ps1`) — everything is automated
3. Create a feature branch: `git checkout -b feat/my-feature`
4. Make your changes and test with `docker compose up --build`
5. Open a PR

---

## License

MIT
