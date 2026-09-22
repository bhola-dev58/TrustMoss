# TrustMoss — C4 Architecture Specification

> **Methodology:** Simon Brown's C4 Model (Context, Container, Component, Code)  
> **Repository:** [https://github.com/bhola-dev58/TrustMoss](https://github.com/bhola-dev58/TrustMoss)  
> **Status:** Approved & Implemented Production Architecture  

---

## 1. Level 1: System Context Diagram

The **System Context** diagram illustrates how TrustMoss fits into the broader enterprise environment, highlighting human personas and external dependencies.

```mermaid
C4Context
    title System Context Diagram for TrustMoss

    Person(user, "End-User / Caller", "Interacts via real-time duplex voice WebRTC or text SSE chat.")
    Person(operator, "Trust & Security Operator", "Audits flagged hallucinations, reviews NLI diffs, and executes 1-click knowledge patches.")

    Enterprise_Boundary(b0, "TrustMoss Enterprise Ecosystem") {
        System(trustmoss, "TrustMoss Platform", "Zero-latency closed-loop trust and reliability gateway for real-time AI agents.")
    }

    System_Ext(moss, "Moss Retrieval Core", "Sub-10ms high-velocity vector search & semantic indexing engine.")
    System_Ext(groq, "Groq Cloud Inference", "Ultra-low latency Llama-3.1-8B Instant inference API.")
    System_Ext(livekit, "LiveKit Cloud SFU", "WebRTC media server for real-time duplex voice streaming.")
    System_Ext(deepgram, "Deepgram Nova-2", "Streaming speech-to-text (STT) audio transcription.")
    System_Ext(cartesia, "Cartesia Sonic", "Streaming text-to-speech (TTS) voice generation.")
    System_Ext(firebase, "Firebase Auth", "Zero-trust JWT authentication and identity management.")

    Rel(user, livekit, "Streams audio turn / voice", "WebRTC / Opus")
    Rel(user, trustmoss, "Sends queries & receives verified answers", "HTTPS / WSS / SSE")
    Rel(operator, trustmoss, "Triages incidents & patches knowledge", "HTTPS / Next.js Console")

    Rel(trustmoss, livekit, "Publishes verified audio & control signals", "WebRTC / LiveKit SDK")
    Rel(trustmoss, moss, "Fetches grounding context & commits patches", "gRPC / REST <10ms")
    Rel(trustmoss, groq, "Streams draft completions", "HTTPS / OpenAI SDK")
    Rel(trustmoss, deepgram, "Streams audio frames for transcription", "WebSocket")
    Rel(trustmoss, cartesia, "Synthesizes verified voice stream", "WebSocket")
    Rel(trustmoss, firebase, "Validates operator & session JWTs", "REST / JWKS")
```

---

## 2. Level 2: Container Diagram

The **Container** diagram decomposes the TrustMoss platform into deployable, independently scalable services, user interfaces, and datastores.

```mermaid
C4Container
    title Container Diagram for TrustMoss Platform

    Person(user, "End-User / Caller", "Interacts via WebRTC voice or web chat.")
    Person(operator, "Trust & Security Operator", "Audits flagged hallucinations and tunes safety thresholds.")

    System_Boundary(c1, "TrustMoss Platform") {
        Container(web_app, "TrustMoss Operations Console", "Next.js 14, React 19, Tailwind CSS", "Single-pane-of-glass HUD, LiveKit WebRTC room, latency waterfall, and HITL workstation.")
        Container(api_gateway, "Trust Gateway Core", "FastAPI, Python 3.11, OpenTelemetry", "Real-time 8-hop trust pipeline, circuit breaker, rate limiting, and autonomous self-healing engine.")
        Container(celery_worker, "Knowledge Ingestion Worker", "Python, Celery, Redis", "Asynchronous index compaction, hard-negative curation, and Moss vector updates.")
        ContainerDb(redis_cache, "Redis L2 Vector Cache & State", "Redis 7 Sentinel", "In-memory cache for sub-2ms hot embeddings, session locks, and rate limit counters.")
        ContainerDb(postgres_db, "Audit & Provenance Ledger", "PostgreSQL 16", "Immutable SHA-256 Merkle audit trail, HITL incident queue, and SOC2/HIPAA compliance records.")
    }

    System_Ext(moss, "Moss Retrieval Core", "Sub-10ms semantic vector store.")
    System_Ext(groq, "Groq Cloud Inference", "High-speed Llama-3.1-8B provider.")
    System_Ext(livekit, "LiveKit SFU", "Duplex audio gateway.")

    Rel(user, web_app, "Interacts with agent & reviews citations", "HTTPS")
    Rel(user, livekit, "Streams duplex audio", "WebRTC")
    Rel(operator, web_app, "Reviews HITL incidents & patches knowledge", "HTTPS")

    Rel(web_app, api_gateway, "Submits queries & streams SSE events", "HTTPS / SSE")
    Rel(web_app, livekit, "Negotiates room tokens", "WSS")

    Rel(api_gateway, moss, "Sub-10ms semantic context query", "REST / gRPC")
    Rel(api_gateway, groq, "Requests prompt synthesis", "HTTPS")
    Rel(api_gateway, redis_cache, "Reads L2 cache & checks locks", "RESP")
    Rel(api_gateway, postgres_db, "Appends immutable audit leaf", "SQL / asyncpg")
    Rel(api_gateway, celery_worker, "Dispatches async re-indexing jobs", "Redis Queue")

    Rel(celery_worker, moss, "Batches vector updates & hot reloads", "REST")
    Rel(celery_worker, postgres_db, "Updates incident resolution status", "SQL")
```

---

## 3. Level 3: Component Diagram (Trust Gateway Core)

Zooming into the **Trust Gateway Core (`api_gateway`)**, this diagram reveals the 8 micro-components executing the synchronous trust loop in under 45ms.

```mermaid
C4Component
    title Component Diagram for Trust Gateway Core

    Container(web_app, "TrustMoss Web App", "Next.js 14", "Client interface.")
    ContainerDb(redis_cache, "Redis L2 Cache", "Redis 7", "Hot embeddings.")
    ContainerDb(postgres_db, "Audit Ledger", "PostgreSQL 16", "Audit logs.")
    System_Ext(moss, "Moss Vector Core", "Vector Engine", "Sub-10ms retrieval.")
    System_Ext(groq, "Groq Inference", "LLM Cloud", "Llama-3.1-8B.")

    Container_Boundary(b1, "Trust Gateway Core (FastAPI)") {
        Component(ingress_ctrl, "Stage 1: Ingress Controller", "FastAPI Router, JWT Guard", "Terminates requests, validates bearer tokens, and assigns W3C traceparents.")
        Component(inbound_sec, "Stage 2: Inbound Guardrail", "Regex & Entropy Scrubber", "Screens for prompt injections and sanitizes inbound PII.")
        Component(retrieval_mgr, "Stage 3: Context Retrieval Manager", "Moss Client, L1/L2 Cache", "Executes sub-10ms top-K chunk lookup with cache fallback.")
        Component(relevance_gate, "Stage 4: Pre-Gen Relevance Gate", "Cosine Distance Filter", "Validates semantic alignment >= 0.70 before triggering LLM.")
        Component(agent_orch, "Stage 5: Agent Orchestrator", "Groq Client, Streaming Buffer", "Injects verified context and streams draft tokens.")
        Component(evaluator_nli, "Stage 6: Groundedness & NLI Evaluator", "DeBERTa-v3 / PyTorch NLI", "Computes token entailment score against retrieved chunks (<5ms).")
        Component(circuit_breaker, "Stage 7: Trust Aggregator & Breaker", "State Machine & Failover", "Calculates composite trust score and triggers autonomous failover.")
        Component(hitl_dispatcher, "Stage 8: HITL Dispatcher & OTel Logger", "Audit Chainer, OTel Exporter", "Constructs SHA-256 Merkle leaf and routes tripped sessions to queue.")
    }

    Rel(web_app, ingress_ctrl, "Submits query / audio transcript", "HTTP POST /api/query")
    Rel(ingress_ctrl, inbound_sec, "Passes sanitized request payload", "In-Process")
    Rel(inbound_sec, retrieval_mgr, "Initiates semantic lookup", "In-Process")
    
    Rel(retrieval_mgr, redis_cache, "Checks L2 cache (<2ms)", "RESP")
    Rel(retrieval_mgr, moss, "Fetches Top-K chunks (<10ms)", "REST / gRPC")
    Rel(retrieval_mgr, relevance_gate, "Sends context chunks & similarity", "In-Process")

    Rel(relevance_gate, agent_orch, "Forwards grounded prompt (Score >= 0.70)", "In-Process")
    Rel(relevance_gate, circuit_breaker, "Signals low relevance trip (Score < 0.60)", "In-Process")

    Rel(agent_orch, groq, "Executes inference", "HTTPS")
    Rel(agent_orch, evaluator_nli, "Streams draft tokens", "In-Process")

    Rel(evaluator_nli, circuit_breaker, "Returns entailment & PII verdict", "In-Process")
    
    Rel(circuit_breaker, ingress_ctrl, "Returns verified response or fallback", "In-Process")
    Rel(circuit_breaker, hitl_dispatcher, "Emits telemetry & breach events", "In-Process")

    Rel(hitl_dispatcher, postgres_db, "Writes SHA-256 audit record", "SQL")
```

---

## 4. Architectural Decisions & Principles (ADR Summary)

1. **Decoupled Safety Fabric:** The LLM does not evaluate its own safety. Groundedness is verified externally by an isolated NLI component in $<5\text{ms}$.
2. **Zero-Latency Retrieval SLA:** Moss provides sub-10ms retrieval, fronted by a local in-memory L1 cache and Redis L2 sentinel replica to ensure guaranteed $<45\text{ms}$ total turn latency.
3. **Autonomous Self-Healing:** Circuit breakers automatically failover to secondary LLM endpoints in $<12\text{ms}$ if Groq latency spikes, while initiating background Moss compaction.
4. **Immutable Cryptographic Ledger:** Every interaction produces a deterministic SHA-256 hash chaining Query, Chunks, Answer, TrustScore, and Operator Commit for SOC2/HIPAA compliance.
