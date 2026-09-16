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

TrustMoss defines **23 Unique Functional Requirement IDs** structured across 6 architectural domains, mapping 1:1 to every layer, microservice, security perimeter, and user interface in the 23-Node Architecture:
* **`FR-SEC-*`**: Enterprise Security & Cryptography (Nodes 1–6)
* **`FR-RT-*`**: Real-Time Reliability & Evaluation (Nodes 7–14)
* **`FR-VOICE-*`**: LiveKit WebRTC Voice Gateway (Nodes 15–17)
* **`FR-MOSS-*`**: Moss Retrieval & Knowledge Lifecycle (Nodes 18–20)
* **`FR-GOV-*`**: Governance, HITL & Prompt Catalog (Nodes 21–22)
* **`FR-UI-*`**: User Interface & Real-Time Reliability HUD (Node 23)

---

### 5.1. Enterprise Security & Cryptography (`FR-SEC-*`)

* **`FR-SEC-01: Inbound Prompt Injection & Adversarial Defense`**
  * **Architecture Node:** Node 1 — Inbound Guardrails Scanner (`services/guardrails_service.py`)
  * **Description:** The system must intercept every inbound prompt prior to knowledge retrieval, executing multidimensional adversarial scanning across prompt injection, jailbreaking, PII exfiltration, and social engineering via `JAILBREAK_ANALYST_V1`.
  * **Contract:** Rejects or sanitizes malicious prompts with threat severity tagging (`SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

* **`FR-SEC-02: Outbound Leakage & PII Redaction`**
  * **Architecture Node:** Node 2 — Outbound Guardrails Scanner (`services/guardrails_service.py`)
  * **Description:** The system must inspect every generated response before egress to prevent credential leaks, API tokens, and personal identifiable information (PII) exfiltration using Microsoft Presidio and regex boundary scanners.
  * **Contract:** Returns `pii_detected: bool`, redacted text, and detected entity classification.

* **`FR-SEC-03: Cryptographic JWT Authentication & RBAC`**
  * **Architecture Node:** Node 3 — JWT & RBAC Auth Engine (`apps/api/auth.py`, `apps/api/main.py`)
  * **Description:** The system must enforce cryptographic token authentication (HS256/RS256) and Role-Based Access Control (`agent`, `reviewer`, `admin`) across all protected endpoints (`/api/query`, `/api/prompts/*`, `/hitl/*`, `/api/compliance/*`).
  * **Contract:** Validates bearer tokens, rejects unsigned or expired claims with HTTP 401, and enforces permission boundaries with HTTP 403.

* **`FR-SEC-04: HTTP Hardening & OWASP Top 10 Headers`**
  * **Architecture Node:** Node 4 — OWASP Security Headers Middleware (`apps/api/main.py`)
  * **Description:** The system must inject OWASP defense-in-depth HTTP security headers on all responses (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy: strict-origin-when-cross-origin`) and enforce CORS origin lockdown.
  * **Contract:** Emits security posture metrics on `/health` and blocks disallowed cross-origin invocations.

* **`FR-SEC-05: Authenticated Data-at-Rest Encryption (AEAD)`**
  * **Architecture Node:** Node 5 — Cryptographic Core (`apps/api/crypto.py`, `services/crypto.py`)
  * **Description:** The system must encrypt sensitive persistent records at rest using AES-256-GCM (NIST SP 800-38D) with 96-bit nonces, 128-bit authentication tags, and Additional Authenticated Data (AAD) binding to thwart ciphertext transplant attacks.
  * **Contract:** Supports atomic EncryptedStore file persistence and field-level encryption for queries, transcripts, and HITL review queues.

* **`FR-SEC-06: GDPR Lifecycle Management & Data Erasure`**
  * **Architecture Node:** Node 6 — GDPR Compliance & Retention Engine (`apps/api/retention.py`, `services/retention.py`)
  * **Description:** The system must provide programmatic compliance with GDPR Article 17 ("Right to Erasure") and Articles 15/20 ("Right of Access / Portability") across session transcripts, audit logs, and HITL queues, alongside configurable TTL-based automated purge sweeps.
  * **Contract:** Exposes `POST /api/compliance/gdpr/erasure`, `GET /api/compliance/gdpr/export/{subject_id}`, and `POST /api/compliance/retention/purge`.

---

### 5.2. Real-Time Reliability & Evaluation (`FR-RT-*`)

* **`FR-RT-01: Synchronous Trust Gateway Ingress Orchestration`**
  * **Architecture Node:** Node 7 — Trust Gateway Orchestrator (`apps/api/main.py`)
  * **Description:** The gateway must coordinate synchronous request-response flow across inbound guardrails, Moss retrieval, pre-generation filtering, agent LLM reasoning, post-generation evaluation, and circuit breaking in a decoupled non-blocking architecture.
  * **Contract:** Serves `POST /api/query` returning answer, composite trust score, tri-state badge, factorized explainability, and microsecond hop latency breakdown.

* **`FR-RT-02: Pre-Generation Context Relevance Gate`**
  * **Architecture Node:** Node 8 — Pre-Generation Relevance Filter (`apps/api/main.py`, `services/moss_service.py`)
  * **Description:** The system must evaluate cosine similarity and semantic overlap of retrieved Moss context chunks against the prompt, discarding any chunk with confidence score below threshold ($\tau = 0.60$) to prevent context poisoning.
  * **Contract:** Passes only verified relevant context chunks to the Agent Orchestrator.

* **`FR-RT-03: Sentence-Level Groundedness & NLI Verification`**
  * **Architecture Node:** Node 9 — Post-Generation Groundedness Evaluator (`services/evaluation_service.py`)
  * **Description:** The system must evaluate generated responses against retrieved Moss context at the individual sentence level using `GROUNDEDNESS_JUDGE_V1` (LLM-as-judge, `temperature=0.05`), classifying each sentence as `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `UNSUPPORTED`.
  * **Contract:** Returns normalized groundedness score (0.0–1.0) and detailed sentence verdict breakdown.

* **`FR-RT-04: Deterministic Hallucination Risk Classification`**
  * **Architecture Node:** Node 10 — Hallucination Risk Classifier (`services/evaluation_service.py`)
  * **Description:** The system must classify hallucination risk into discrete tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) using `HALLUCINATION_RISK_V1` (`temperature=0.0`), mapping each tier to an automated `recommended_action` and `hitl_priority`.
  * **Contract:** Emits structured risk classification within the `/evaluate` payload.

* **`FR-RT-05: Tri-State Trust Aggregator & Reliability Scoring`**
  * **Architecture Node:** Node 11 — Trust Score Aggregator (`apps/api/main.py`, `services/evaluation_service.py`)
  * **Description:** The system must compute a weighted composite trust score ($S = 0.40 \times \text{Groundedness} + 0.30 \times \text{Relevance} + 0.20 \times \text{PII} + 0.10 \times \text{Safety}$) and assign tri-state verdicts:
    * **PASS (Green):** Relevance $\ge 0.70$, Groundedness $\ge 0.70$, zero PII detected.
    * **WARN (Yellow):** Exactly one metric below threshold; serve response with cautionary disclaimer.
    * **FAIL (Red):** Two or more metrics below threshold OR any PII/jailbreak detected.
  * **Contract:** Returns composite score (0.0–1.0), letter grade (A–F), and status enum.

* **`FR-RT-06: Dynamic Circuit Breaker & Zero-Leak Fallback`**
  * **Architecture Node:** Node 12 — Dynamic Circuit Breaker (`apps/api/main.py`)
  * **Description:** Upon a `FAIL` verdict or critical security breach, the circuit breaker must immediately suppress the raw model response within $< 10\text{ ms}$, substituting a safe deterministic fallback message and routing the transaction to HITL.
  * **Contract:** Guarantees zero ungrounded or compromised token leakage to end users.

* **`FR-RT-07: Microsecond 8-Hop Distributed Latency Tracing`**
  * **Architecture Node:** Node 13 — OTel Latency Tracer & Hop Instrumentation (`apps/api/main.py`, `apps/api/voice_gateway.py`)
  * **Description:** The system must record microsecond-precision timestamps for all 8 synchronous hops:
    $$\Delta t_{\text{total}} = \Delta t_{\text{inbound}} + \Delta t_{\text{moss}} + \Delta t_{\text{relevance}} + \Delta t_{\text{llm}} + \Delta t_{\text{groundedness}} + \Delta t_{\text{outbound}} + \Delta t_{\text{circuit}} + \Delta t_{\text{gateway}}$$
  * **Contract:** Injects `latency_ms` per-hop dictionary into every API response and OpenTelemetry trace span.

* **`FR-RT-08: Multidimensional Trust Score Explainability`**
  * **Architecture Node:** Node 14 — Factorized Trust Explainability Engine (`apps/api/explainability.py`)
  * **Description:** The system must generate factorized explanations (`FactorExplanation`) across context relevance, groundedness, PII safety, and bias/toxicity, citing retrieved Moss context chunks, confidence levels, and actionable operator recommendations.
  * **Contract:** Exposes `GET /api/explain/{query_id}` and embeds explanation in `POST /api/query`.

---

### 5.3. LiveKit WebRTC Voice Gateway (`FR-VOICE-*`)

* **`FR-VOICE-01: Authenticated WebRTC Room & Token Provisioning`**
  * **Architecture Node:** Node 15 — LiveKit Token Service (`apps/api/livekit_service.py`)
  * **Description:** The system must issue cryptographically signed WebRTC JWT access tokens with scoped VideoGrants (`room_join`, `can_publish`, `can_subscribe`) for secure client room ingress.
  * **Contract:** Serves `POST /api/livekit/token` validating client credentials and session parameters.

* **`FR-VOICE-02: Real-Time Audio Interception & Circuit Breaker`**
  * **Architecture Node:** Node 16 — Voice Gateway & Audio Interceptor (`apps/api/voice_gateway.py`)
  * **Description:** The system must intercept streaming speech transcripts, execute asynchronous guardrails and groundedness validation, and trigger an audio circuit breaker within $< 20\text{ ms}$ if trust thresholds are violated.
  * **Contract:** Serves `POST /api/voice/process-transcript` and mutes audio output upon safety breaches.

* **`FR-VOICE-03: Autonomous LiveKit Voice Agent Worker`**
  * **Architecture Node:** Node 17 — Autonomous LiveKit Voice Worker (`apps/api/livekit_agent_worker.py`)
  * **Description:** The system must operate a headless WebRTC worker using `livekit-agents` and `VOICE_AGENT_V1` CRISPE prompt, delivering conversational speech-to-speech interaction capped at 256 tokens in TTS-optimized prose without markdown formatting.
  * **Contract:** Connects to LiveKit SFU, subscribes to user audio tracks, and publishes synthesized voice responses.

---

### 5.4. Moss Retrieval & Knowledge Lifecycle (`FR-MOSS-*`)

* **`FR-MOSS-01: Sub-15ms Hybrid Context Retrieval`**
  * **Architecture Node:** Node 18 — Moss Retrieval Engine Core (`services/moss_service.py`)
  * **Description:** The system must execute hybrid sparse-dense vector retrieval against the indexed enterprise knowledge base, extracting top-$k$ contextual evidence chunks with a P95 latency $< 15\text{ ms}$.
  * **Contract:** Serves `POST /retrieve` returning ranked chunks with cosine confidence scores and retrieval latency metrics.

* **`FR-MOSS-02: Asynchronous Knowledge Ingestion Pipeline`**
  * **Architecture Node:** Node 19 — Knowledge Ingestion Pipeline (`apps/api/main.py`, `services/moss_service.py`)
  * **Description:** The system must process reviewer-approved answers asynchronously, embedding and re-indexing corrected knowledge into a staged Moss index partition without blocking the primary request path.
  * **Contract:** Handles `POST /hitl/resolve` triggering background index updates.

* **`FR-MOSS-03: Semantic Commit Snapshotting & Atomic Rollback`**
  * **Architecture Node:** Node 20 — Index Version Registry & Rollback Manager (`services/moss_service.py`)
  * **Description:** The system must maintain an immutable registry of Moss index snapshots keyed by semantic commit hashes, supporting zero-downtime blue/green pointer swapping and instantaneous atomic rollback to previous known-good commits.
  * **Contract:** Enforces Sanity Eval Gates (Groundedness $\ge 0.85$, zero security regressions, P95 latency $< 50\text{ ms}$) prior to production activation.

---

### 5.5. Governance, HITL & Prompt Catalog (`FR-GOV-*`)

* **`FR-GOV-01: Human-in-the-Loop Review Queue & Reviewer Verdicts`**
  * **Architecture Node:** Node 21 — HITL Review Queue & Anomaly Alerting (`apps/api/main.py`, `services/evaluation_service.py`)
  * **Description:** The system must automatically route transactions flagged as `WARN` or `FAIL` into an AES-256-GCM encrypted review queue, generating structured decision records via `HITL_VERDICT_V1` with `trust_delta`, changes made, and GDPR compliance audit logging.
  * **Contract:** Exposes `GET /hitl/queue`, `GET /hitl/queue/raw`, and `POST /hitl/resolve`.

* **`FR-GOV-02: Enterprise CRISPE Prompt Catalog & Live Discovery`**
  * **Architecture Node:** Node 22 — CRISPE Prompt Catalog & Template Registry (`apps/api/prompts/catalog.py`, `crispe.py`, `evaluation.py`)
  * **Description:** The system must govern all 7 LLM call surfaces via versioned CRISPE templates (Capacity, Request, Insight, Style, Persona, Execute), auto-synchronize live metadata on API startup into `docs/PROMPT_CATALOG.md`, and provide authenticated runtime discovery endpoints.
  * **Contract:** Exposes `GET /api/prompts/catalog` and `GET /api/prompts/catalog/{template_name}`.

---

### 5.6. User Interface & Real-Time Reliability HUD (`FR-UI-*`)

* **`FR-UI-01: Next.js 14+ Real-Time Reliability HUD & Operations Console`**
  * **Architecture Node:** Node 23 — Next.js App Router Reliability HUD (`apps/web/`)
  * **Description:** The system must provide a server-rendered (SSR) Next.js 14+ dashboard featuring live Tri-State Trust Badges (Green/Yellow/Red), an 8-hop microsecond latency waterfall bar chart, cited Moss context source cards, a factorized Trust Score Explainability drawer, an interactive LiveKit WebRTC audio room with voice reliability HUD, and an operator HITL review interface.
  * **Contract:** Proxies requests securely through Next.js API routes (`/api/gateway/*`) preventing client credential exposure.

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
