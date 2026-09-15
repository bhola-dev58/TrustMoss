# Product Requirements Document (PRD): TrustMoss

## 1. Executive Summary
**TrustMoss** is a high-integrity reliability and security gateway designed for AI agents. It provides a multi-layered "trust loop" that validates agent inputs and outputs in real-time. By integrating **Moss** for high-speed retrieval and **Groq (Llama-3.1)** for reasoning, TrustMoss ensures that enterprise AI agents are secure, grounded in factual context, and continuously improving through human-in-the-loop (HITL) feedback and automated knowledge versioning.

## 2. Problem Statement
AI agents in enterprise environments face three critical challenges:
1. **Unreliability:** Hallucinations and lack of groundedness in retrieved context.
2. **Security Risks:** Exposure of PII and vulnerability to prompt injection attacks.
3. **Lack of Governance:** Difficulty in auditing agent decisions and safely updating the knowledge base without regressions.

## 3. Goals & Objectives
* **Real-time Safety:** Block 100% of detected PII and prompt injections before they reach the LLM or the user.
* **High Groundedness:** Maintain a minimum groundedness score of 0.85 for production-promoted knowledge.
* **Performance:** Achieve P95 retrieval latency of < 50ms using Moss.
* **Operational Transparency:** Provide microsecond-level "per-hop" latency tracing for every request.
* **Self-Correction:** Establish a closed-loop system where human corrections directly update the retrieval index.

## 4. Target Users / Stakeholders
* **AI Engineers:** Building and deploying RAG-based agents.
* **Security & Compliance Officers:** Monitoring for data leaks and prompt safety.
* **Operations Managers:** Reviewing agent performance and managing knowledge versioning.

## 5. Functional Requirements

### 5.1. Real-Time Sync Pipeline
* **Inbound Guardrails:** Scrub prompts for injections and PII using Microsoft Presidio and Guardrails AI.
* **Contextual Retrieval:** Fetch relevant chunks via Moss Retrieval Engine.
* **Pre-Generation Relevance Filter:** Discard low-confidence context chunks before they reach the Agent Orchestrator.
* **Post-Generation Evaluation:** Perform NLI-based groundedness checks against the original Moss context.
* **Tri-State Trust Aggregator:**
  * **PASS (Green):** Context Relevance $\ge$ 0.7, Groundedness $\ge$ 0.7, Zero PII.
  * **WARN (Yellow):** Exactly 1 check fails; serve response with a disclaimer.
  * **FAIL (Red):** 2+ checks fail OR any PII detected; trigger Circuit Breaker to return a safe fallback.

### 5.2. Human-in-the-Loop (HITL) & Feedback
* **Review Queue:** Automatically route FAIL/WARN queries to a manual review interface.
* **Knowledge Ingestion:** Allow operators to approve corrected answers, triggering an async update to the Moss index.
* **Audit Marking:** Mark resolved entries as "Approved" in the Audit Store.

### 5.3. Knowledge Governance
* **Index Version Registry:** Maintain immutable snapshots of Moss indices with semantic commit hashes.
* **Version Manager:** Support zero-downtime atomic rollbacks to previous index versions.
* **Sanity Eval Gate:** Prevent promotion of new indices unless they meet:
  * Groundedness $\ge$ 0.85 on golden queries.
  * Zero security regressions.
  * P95 Retrieval Latency < 50ms.

## 6. Non-Functional Requirements
* **Performance:** Per-hop latency must be captured at microsecond resolution.
* **Reliability:** Circuit breaker must suppress untrusted content within < 10ms of evaluation.
* **Scalability:** Async processing for telemetry and knowledge ingestion to prevent blocking the main request path.
* **Observability:** Full OpenTelemetry integration for distributed tracing.

## 7. System Architecture Overview
The system is divided into four primary groups:
1. **Trust Core:** Handles the sync request flow, guardrails, and the Trust Aggregator.
2. **Retrieval Layer:** Manages Moss indices, versioning, and atomic rollbacks.
3. **Feedback Loop:** Manages HITL reviews and the ingestion pipeline.
4. **Operations:** Handles OTel collection, audit logging, and automated alerting.

## 8. Tech Stack
* **Frontend:** Next.js 14+ (App Router), React 18/19, Tailwind CSS, LiveKit Components React.
* **Voice Gateway:** LiveKit Cloud / SFU (WebRTC), `livekit-agents` (Python worker), Deepgram STT, Cartesia TTS.
* **Backend/Orchestration:** FastAPI, Python 3.12, Pydantic v2, Celery / Redis.
* **AI/Inference:** Groq (Llama-3.1-8B), Moss SDK (~11ms retrieval).
* **Security/Eval:** Guardrails AI, Microsoft Presidio, Ragas.
* **Data/Storage:** PostgreSQL (Audit/HITL), ClickHouse (Telemetry), Redis (Queue), Moss Native Index.
* **Observability:** OpenTelemetry (8-hop audio & text tracing), Prometheus, Grafana.

## 9. Data Requirements
* **Audit Store:** Stores the "Triplet" (Prompt, Moss Context, Agent Response) + Trust Scores.
* **Golden Dataset Store:** Curated reference queries and ground-truth answers for benchmarking.
* **Index Version Registry:** Metadata for Moss snapshots, including commit hashes and evaluation results.

## 10. API Specifications
* `POST /query`: Primary endpoint for agent interaction. Returns response + Trust Verdict + latency trace.
* `POST /api/livekit/token`: Issues authenticated WebRTC JWT access tokens with VideoGrants.
* `POST /api/voice/process-transcript`: Real-time voice transcript processing through Trust Gateway with audio circuit breaker.
* `GET /history`: Retrieves session interactions for review.
* `GET /health`: Liveness and readiness probe for the gateway and Moss index.

## 11. Security Requirements
* **Data Protection:** Mandatory PII masking on both inbound prompts and outbound responses.
* **Integrity:** Immutable audit logs for all "FAIL" state triggers.

## 12. Deployment & Infrastructure
* **Backend Deployment:** Decoupled Microservices in Docker Compose / Render / Railway.
* **Frontend Deployment:** Next.js Standalone Container in Docker Compose / Vercel.
* **CI/CD for Knowledge:** Automated Sanity Eval Gate integrated into the Knowledge Ingestion Pipeline.

## 13. Success Metrics (KPIs)
* **Groundedness Score:** $\ge$ 0.85 average across production traffic.
* **System Health:** FAIL rate $< 5\%$ over a rolling 5-minute window.
* **Latency:** P95 Moss Retrieval $< 50ms$ (benchmarked at ~11ms).
* **Security:** Zero PII leaks in "PASS" or "WARN" responses.

## 14. Timeline & Milestones
* **Phase 1 (MVP):** Core Moss retrieval + Agent Orchestrator + Web UI (Completed).
* **Phase 2 (Trust):** Guardrails Service + Evaluation Engine + Tri-state Aggregator (Completed).
* **Phase 3 (Ops):** OTel instrumentation + Alerting Manager + Audit Store (Completed).
* **Phase 4 (Governance):** HITL Queue + Knowledge Ingestion + Index Versioning (Completed).

## 15. Open Questions & Risks
* **Real-time Evaluation Overhead:** Addressed by using Moss's ultra-fast 11ms retrieval, leaving maximum budget for evaluation.
* **Cold Start on Index Swaps:** Addressed by the Version Manager's atomic blue/green pointer swap.
