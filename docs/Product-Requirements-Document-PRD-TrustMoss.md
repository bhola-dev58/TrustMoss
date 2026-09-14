# Product Requirements Document (PRD): TrustMoss

## 1. Executive Summary
**TrustMoss** is an enterprise-grade Trust, Security, and Reliability Gateway designed to wrap AI agents in a high-integrity safety fabric. By leveraging **Moss** as a high-performance retrieval core, TrustMoss ensures that agentic workflows are grounded in authoritative context, protected against security threats, and subject to continuous real-time and offline evaluation. The system features a closed-loop feedback mechanism where human-in-the-loop (HITL) corrections directly improve the underlying knowledge base through a versioned deployment pipeline.

## 2. Problem Statement
Enterprises deploying AI agents face three critical barriers:
1.  **Unreliability:** Hallucinations and lack of groundedness in enterprise data.
2.  **Security Risks:** Vulnerabilities to prompt injection, jailbreaking, and accidental PII leakage.
3.  **Lack of Observability:** Difficulty in tracing the "reasoning chain" and measuring the latency/cost of multi-hop agentic processes.

TrustMoss solves these by providing a "Trust Layer" that sits between the user and the LLM, enforcing strict reliability gates and security guardrails.

## 3. Goals & Objectives
*   **Groundedness:** Ensure agent responses strictly adhere to retrieved context (Moss).
*   **Security:** Provide 100% mitigation for known prompt injections and PII leaks.
*   **Operational Excellence:** Maintain P95 retrieval latency under 50ms.
*   **Self-Improvement:** Enable a seamless HITL workflow to turn agent failures into "Golden" training data.
*   **Governance:** Implement "Git-like" version control for the knowledge base to allow atomic rollbacks.

## 4. Target Users / Stakeholders
*   **AI Engineers:** To build and debug reliable agentic workflows.
*   **Security & Compliance Officers:** To monitor for PII leaks and policy violations.
*   **Product Managers:** To track trust metrics and system performance.
*   **Subject Matter Experts (SMEs):** To review and annotate agent responses in the HITL queue.

## 5. Functional Requirements

### 5.1. Real-Time Reliability Pipeline (Sync)
*   **Inbound Guardrails:** Must detect and block prompt injections and jailbreak attempts. Must redact PII from user queries before they reach the retrieval layer.
*   **Moss Retrieval:** Must perform hybrid search (vector + keyword) to fetch relevant context chunks.
*   **Pre-Generation Relevance Filter:** Must evaluate retrieved Moss chunks and discard those with low confidence to prevent "context poisoning."
*   **Post-Generation Groundedness Check:** Must perform NLI (Natural Language Inference) and token-overlap analysis to verify the response against Moss context.
*   **Outbound PII Scanner:** Must verify that the generated response contains no sensitive enterprise data.

### 5.2. Trust Aggregator & Circuit Breaker
*   **Tri-State Scoring Logic:**
    *   **PASS (Green):** Context Relevance $\ge$ 0.7, Groundedness $\ge$ 0.7, and Zero PII detected.
    *   **WARN (Yellow):** Exactly one check fails (e.g., low relevance). Serve response with a disclaimer.
    *   **FAIL (Red):** Two or more checks fail OR any PII is detected. Trigger Circuit Breaker to block output and return a safe fallback.

### 5.3. Operations & HITL
*   **HITL Review Queue:** Automatically route FAIL/WARN queries with severe mismatches for manual audit.
*   **Knowledge Ingestion:** Allow operators to approve corrected answers, which are then asynchronously re-indexed into Moss.
*   **Anomaly Alerting:** Trigger alerts (Slack/PagerDuty) if FAIL rate > 5% over a 5-minute window or average Groundedness < 0.65.

### 5.4. Knowledge Governance
*   **Index Version Registry:** Snapshot every Moss update with a semantic commit hash.
*   **Sanity Eval Gating:** New index versions must pass a "Sanity Eval" before promotion:
    *   Groundedness $\ge$ 0.85 on golden queries.
    *   Zero regressions on security benchmarks.
    *   P95 Retrieval Latency < 50ms.
*   **Atomic Rollback:** Support one-click restoration of previous known-good index versions.

## 6. Non-Functional Requirements
*   **Performance:** Per-hop latency must be tracked at the microsecond level.
*   **Scalability:** Ingestion and continuous evaluation must run as asynchronous background workers.
*   **Reliability:** The system must support zero-downtime index updates.
*   **Auditability:** All prompt-context-response triplets must be stored in an immutable audit store.

## 7. System Architecture Overview
The architecture is divided into seven functional layers:
1.  **Client Layer:** Next.js dashboard for monitoring and HITL.
2.  **Gateway & Security Layer:** FastAPI gateway and Guardrails service.
3.  **Agent Core Layer:** LangGraph orchestrator using Groq/Llama-3.1.
4.  **Reliability & Eval Layer:** Real-time scoring and offline benchmarking.
5.  **Knowledge Lifecycle Layer:** Versioning, ingestion, and sanity gating.
6.  **Observability Layer:** OTel collector and Audit Store.
7.  **Operations Layer:** Alerting and HITL management.

## 8. Tech Stack
*   **Frontend:** Next.js, React, Tailwind CSS, Tremor UI.
*   **API/Backend:** FastAPI, Python, Pydantic, Redis.
*   **Agent Orchestration:** LangGraph, Groq, Llama-3.1.
*   **Retrieval Engine:** Moss (Core), Moss SDK.
*   **Security:** Guardrails AI, Microsoft Presidio, NeMo Guardrails.
*   **Evaluation:** Ragas, DeepEval, Arize Phoenix.
*   **Databases:** PostgreSQL (Audit/Metadata), ClickHouse (Telemetry), Redis (Caching/Queue), S3 (Snapshots).
*   **Observability:** OpenTelemetry, Prometheus, Grafana, Jaeger.

## 9. Data Requirements
*   **Interaction Triplets:** Storage of (User Prompt, Retrieved Moss Context, Agent Response).
*   **Trust Metadata:** Verdicts (Pass/Warn/Fail), individual scores, and PII detection logs.
*   **Golden Datasets:** Curated reference sets for benchmarking and sanity gating.
*   **Version Registry:** Metadata for index snapshots (Commit Hash, Timestamp, Eval Scores).

## 10. API Specifications
*   **POST `/v1/agent/query`:** Main entry point for client requests.
*   **GET `/v1/trust/metrics`:** Returns real-time trust scores and latency breakdown.
*   **POST `/v1/hitl/approve`:** Submits a corrected response to the ingestion pipeline.
*   **POST `/v1/version/rollback`:** Triggers an atomic rollback to a specific commit hash.

## 11. Security Requirements
*   **Authentication:** Auth0 integration for the Trust Gateway and UI.
*   **Data Protection:** Inbound/Outbound PII masking.
*   **Audit Trail:** Immutable logging of all security verdicts in the Audit Store.

## 12. Deployment & Infrastructure
*   **Cloud:** AWS/GCP/Azure compatible.
*   **Containerization:** Docker/Kubernetes for all microservices.
*   **Async Processing:** Celery with Redis for ingestion and continuous evaluation tasks.

## 13. Success Metrics
*   **Groundedness Rate:** Percentage of responses with Groundedness $\ge$ 0.85.
*   **Security Efficacy:** 0% PII leakage in production.
*   **Retrieval Speed:** P95 Moss latency < 50ms.
*   **HITL Throughput:** Time taken from "Flagged" to "Re-indexed" in Moss.

## 14. Timeline & Milestones
*   **Phase 1 (MVP):** Trust Gateway, Moss Retrieval, and Basic Tri-State Scoring.
*   **Phase 2 (Security & Ops):** Inbound/Outbound Guardrails, OTel Tracing, and Alerting Manager.
*   **Phase 3 (Governance):** HITL Review Queue, Knowledge Ingestion Pipeline, and Index Versioning.
*   **Phase 4 (Optimization):** Sanity Eval Gating and automated Golden Dataset drift detection.

## 15. Open Questions & Risks
*   **Model Drift:** How frequently should the Golden Dataset be updated to reflect changing business logic?
*   **Latency Overhead:** The cumulative latency of multiple guardrail and evaluation hops must be monitored to ensure it doesn't degrade user experience.
*   **Cost:** Token usage for real-time evaluation (Ragas/DeepEval) needs to be optimized.