# Product Requirements Document (PRD): TrustMoss

## 1. Executive Summary
**TrustMoss** is a high-performance architectural framework designed to solve the critical challenges of **Agent Reliability, Security, and Evaluation**. By integrating ultra-fast retrieval (Moss), real-time voice orchestration (LiveKit), and a multi-layered governance engine, TrustMoss provides a "Glass Box" environment for AI agents. The system ensures that every interaction is scanned for security, validated for groundedness, and traced with microsecond precision, all while maintaining the low-latency requirements necessary for natural human-agent voice conversation.

## 2. Problem Statement
AI agents, particularly in voice-first applications, face three primary hurdles to enterprise adoption:
1.  **Unreliability:** Hallucinations and lack of groundedness in real-time.
2.  **Security Risks:** Vulnerability to prompt injection, jailbreaking, and PII leakage.
3.  **Latency:** Safety guardrails often introduce delays that break the flow of natural conversation.

TrustMoss solves these by implementing sub-millisecond safety gates and a verifiable traceability matrix.

## 3. Goals & Objectives
*   **Zero-Trust Interaction:** 100% interception of adversarial inputs and PII redaction.
*   **Ultra-Low Latency:** Maintain a total voice turn overhead of <350ms.
*   **Verifiable Groundedness:** Achieve a 0.70+ groundedness score using NLI-based evaluation.
*   **Operational Transparency:** Provide 8-hop microsecond tracing for every agent decision.
*   **Continuous Compliance:** Automated GDPR-compliant audit logs and HITL (Human-in-the-Loop) workflows.

## 4. Target Users / Stakeholders
*   **AI Product Managers:** To monitor agent performance and trust metrics.
*   **Security & Compliance Officers:** To audit interactions and manage GDPR data erasure.
*   **AI Engineers:** To debug latency bottlenecks and refine prompt catalogs.
*   **Human Reviewers:** To resolve flagged interactions via the HITL queue.

## 5. Functional Requirements

### 5.1 Security & Compliance (FR-SEC)
*   **FR-SEC-01:** Inbound adversarial scanner to intercept 100% of jailbreak and injection attempts.
*   **FR-SEC-02:** Outbound PII redaction with an immediate circuit breaker trip if sensitive data is detected.
*   **FR-SEC-03:** JWT/RBAC authentication engine with sub-2ms rejection for unauthorized requests.
*   **FR-SEC-04:** Enforcement of OWASP Top 10 security headers and strict CORS lockdown.
*   **FR-SEC-05:** AES-256-GCM AEAD encryption for all data at rest (Audit Store, HITL Queue, Index Registry).
*   **FR-SEC-06:** GDPR Article 17 compliance via automated erasure and TTL-based data purges.

### 5.2 Real-Time Performance (FR-RT)
*   **FR-RT-01:** Ingress orchestration overhead capped at 45ms P95.
*   **FR-RT-02:** Pre-generation context relevance filtering using a 0.60 cosine threshold.
*   **FR-RT-03:** Sentence-level groundedness scoring (NLI-based).
*   **FR-RT-04:** Deterministic hallucination risk classification (LOW/MED/HIGH/CRIT).
*   **FR-RT-05:** 4-factor composite trust scoring (Security, Groundedness, Relevance, Risk).
*   **FR-RT-06:** Sub-10ms raw token suppression circuit breaker.
*   **FR-RT-07:** Microsecond-level 8-hop tracing integrated with OpenTelemetry.
*   **FR-RT-08:** Factorized explainability retrieval in <5ms for every blocked/flagged action.

### 5.3 Voice & Audio (FR-VOICE)
*   **FR-VOICE-01:** LiveKit WebRTC JWT token issuance in under 15ms.
*   **FR-VOICE-02:** Sub-20ms audio circuit breaker to sever streams upon safety violations.
*   **FR-VOICE-03:** Autonomous voice agent capped at 256 tokens per turn to ensure conciseness.

### 5.4 Knowledge & Retrieval (FR-MOSS)
*   **FR-MOSS-01:** Moss hybrid retrieval (Vector + Keyword) benchmarked at ~11ms (sub-15ms target).
*   **FR-MOSS-02:** Asynchronous background re-indexing with 0ms read penalty during updates.
*   **FR-MOSS-03:** Immutable SHA-256 index snapshots with sub-100ms atomic rollbacks.

### 5.5 Governance & UI (FR-UI / FR-GOV)
*   **FR-UI-01:** Next.js 14+ SSR dashboard with sub-1.2s FCP, featuring Tri-State Trust Badges and Audio Waveform HUDs.
*   **FR-GOV-01:** Encrypted HITL review queue generating `HITL_VERDICT_V1` decision records.
*   **FR-GOV-02:** Centralized CRISPE prompt catalog governing all 7 LLM surfaces with zero-drift doc syncing.

### 5.6 Performance & Scalability (FR-PERF)
*   **FR-PERF-01:** k6 OSS Scalability Testing Engine supporting 5 profiles (`load`, `ramp`, `stress`, `spike`, `soak`) with automated simulation fallback.
*   **FR-PERF-02:** Strict sub-45ms P95 latency and sub-1% error SLA gating assertions.
*   **FR-PERF-03:** Non-blocking background subprocess execution with real-time cancellation (`SIGTERM`).
*   **FR-PERF-04:** PostgreSQL 16 relational benchmark persistence and Next.js live telemetry dashboard.

## 6. Non-Functional Requirements
*   **Scalability:** Horizontal scaling of FastAPI services and LiveKit workers.
*   **Reliability:** 99.5% room availability for voice sessions.
*   **Maintainability:** 100% bidirectional verification linking nodes to requirements (Traceability Matrix).
*   **Observability:** Structured JSON logging and OTel-compatible trace exports.

## 7. System Architecture Overview
The system is divided into seven logical layers:
1.  **Frontend & UI Layer:** Next.js dashboard for monitoring and HITL.
2.  **Edge & Security Perimeter:** Trust Gateway and LiveKit SFU for ingress/auth.
3.  **Agent Core & Governance:** Orchestrator, Evaluation Service, and CRISPE Catalog.
4.  **Knowledge & Retrieval Layer:** Moss SDK and Vector Store.
5.  **Governance, Audit & Observability:** OTel Collector, Audit Store, and Alerting.
6.  **DevOps & Infrastructure:** Docker networking and setup automation.
7.  **Automation Layer:** CI/CD pipelines for testing and integration.

## 8. Tech Stack
*   **Backend:** FastAPI (Python 3.11), LangGraph, Moss SDK.
*   **Frontend:** Next.js 14+ (App Router), Tailwind CSS, LiveKit Components.
*   **AI/LLM:** Groq (Llama-3.1-8B), Deepgram (STT), Cartesia (TTS).
*   **Database/Storage:** ClickHouse (Audit), PostgreSQL (HITL/Registry), Redis (Caching/LiveKit).
*   **Security:** Guardrails AI, Microsoft Presidio, Bandit (SAST).
*   **DevOps:** Docker, Docker Compose, GitHub Actions.

## 9. Data Requirements
*   **Audit Store:** Encrypted logs of every interaction, including 8-hop traces.
*   **Index Registry:** Versioned metadata for Moss indices with SHA-256 hashes.
*   **HITL Queue:** Structured records (`HITL_VERDICT_V1`) for human review.
*   **Retention:** Automated TTL purges (e.g., 7-day transcript retention) for GDPR compliance.

## 10. API Specifications
*   **POST /api/auth/token:** JWT issuance (FR-SEC-03).
*   **GET /health:[8000-8003]:** Health probes for Gateway, Guardrails, Moss, and Evaluation.
*   **WebRTC Signaling:** LiveKit-compatible signaling for real-time audio.
*   **Discovery API:** Sub-5ms prompt discovery from the CRISPE Catalog.

## 11. Security Requirements
*   **Defense-in-Depth:** Multi-stage scanning (Inbound -> Orchestration -> Outbound).
*   **Tamper-Proofing:** 96-bit random nonces for AES-256-GCM to ensure data integrity.
*   **RBAC:** Granular access control for HITL reviewers vs. system admins.

## 12. Deployment & Infrastructure
*   **Containerization:** Multi-stage Docker builds for lean production images.
*   **Orchestration:** Docker Compose for local and staging environments.
*   **CI/CD:** 
    *   `test`: 247-test pytest suite with 70% coverage gate.
    *   `lint`: Ruff static analysis.
    *   `security`: Bandit SAST + Pip-audit supply chain scanner.
    *   `frontend`: Next.js 14 standalone build + 10 Vitest component tests.
    *   `k6-sla-gate`: Automated sub-45ms P95 latency and error rate gate.

## 13. Success Metrics (KPIs)
*   **Latency:** Moss retrieval < 15ms; Gateway < 45ms (P95).
*   **Safety:** 0% PII leakage in production tests.
*   **Quality:** 257/257 passing tests (100% green across backend & frontend).
*   **UX:** Dashboard FCP < 1.2s.

## 14. Timeline & Milestones
*   **Phase 7.1:** CI/CD Pipeline Layer (Completed).
*   **Phase 7.2:** Docker Build & Integration Smoke Tests (Completed).
*   **Phase 8:** Advanced Red-Teaming & Adversarial Simulation (Upcoming).
*   **Phase 9:** Final Submission & Documentation Freeze.

## 15. Open Questions & Risks
*   **Risk:** Latency drift in high-concurrency scenarios. *Mitigation: OTel-based alerting.*
*   **Risk:** Cost of high-frequency NLI evaluation calls. *Mitigation: Use of Groq/Llama-3.1-Instant for cost-effective scoring.*
*   **Question:** Should the 256-token cap be dynamic based on user intent? (Currently fixed).