# TrustMoss 🛡️🌿

> **Real-Time Trust, Security & Reliability Gateway for AI Agents**  
> *YC Fall 2026 x Moss: Zero Latency Builder Sprint — Track: Agent Reliability, Security & Evaluation*

---

## 📌 Overview

**TrustMoss** is an enterprise runtime trust and guardrail gateway that sits between an AI agent's retrieval step and response generation. Leveraging **Moss** as the low-latency contextual retrieval layer, TrustMoss evaluates every interaction in real-time, executing pre-generation and post-generation safety checks to issue a live **Trust Score** and prevent hallucinations before answers reach users.

---

## 🏛️ Architecture

Detailed architecture specifications and PDF diagrams:
- **Architecture Spec:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Architecture Diagram (PDF):** [`docs/architecture_diagram.pdf`](docs/architecture_diagram.pdf)
- **Product Requirements Document (PRD):** [`docs/PRD.md`](docs/PRD.md)

### Key Subsystems
1. **Client & Trust Gateway (FastAPI / Next.js):** Rate limiting, authentication, payload sanitization, and request tracing.
2. **Inbound Guardrails:** Intercepts prompt injection attacks, jailbreaks, and scrubs user PII.
3. **Moss Retrieval Core:** Ultra-low-latency semantic retrieval and hybrid search for enterprise context.
4. **Pre-Generation Relevance Gate:** Filters out low-confidence chunks before passing context to the LLM.
5. **Agent Orchestrator:** Groq / Llama-3.1 context-grounded reasoning.
6. **Post-Generation Groundedness & PII Filter:** Strict NLI and token overlap comparison against Moss context chunks.
7. **Tri-State Trust Aggregator & Circuit Breaker:**
   - **PASS (Green):** Relevance $\ge$ 0.7, Groundedness $\ge$ 0.7, Zero PII.
   - **WARN (Yellow):** Single borderline metric; served with a disclaimer badge.
   - **FAIL (Red):** Severe hallucination or PII leak; Circuit Breaker trips to return a safe fallback.
8. **Human-in-the-Loop (HITL) & Knowledge Versioning:** Flagged outputs enter an audit queue; approved corrections are re-indexed into Moss under semantic commit hashes with zero-downtime rollback capability.
9. **Observability & Telemetry:** OpenTelemetry tracing across all hops (Moss vs. Guardrails vs. LLM) and automated anomaly alerting.

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- Groq API Key
- Moss API Key

### 2. Backend Setup
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Backend API
```bash
uvicorn main:app --reload --port 8000
```

### 4. API Endpoints
- `POST /query`: Run full retrieval $\to$ guardrails $\to$ LLM $\to$ trust scoring pipeline.
- `GET /history`: View session query history and latency breakdowns.
- `GET /health`: Liveness check.

---

## 📄 License
MIT
