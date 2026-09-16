# TrustMoss CRISPE Prompt Catalog

> **Auto-generated from `TEMPLATE_REGISTRY`** — do not edit manually.
> Generated: 2026-09-16T17:48:57.269552+00:00  |  Catalog Version: 1.0.0

## Overview

TrustMoss uses **7 versioned CRISPE prompt templates** to govern every LLM interaction across the platform.
All templates are named, versioned (SemVer), and registered in a shared `TEMPLATE_REGISTRY` for auditability and replay.

| Category | Count |
|---|---|
| `orchestration` | 2 |
| `governance` | 2 |
| `evaluation` | 2 |
| `safety` | 1 |

---

## `ORCHESTRATOR_V1` (v1.0.0)

**Category:** `orchestration`  |  **Task:** Task 5.1  |  **PRD:** Section 4.1 — Agent Orchestration

**LLM Surface:** `apps/api/main.py → POST /api/query → call_llm()`

| Parameter | Value |
|---|---|
| Temperature | `0.2` |
| Max Tokens | `512` |
| Output Format | `prose` |
| TTS Safe | `False` |

**Guardrails:** `context_relevance`, `groundedness`, `pii_safety`, `bias_toxicity`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Enterprise RAG knowledge assistant — TrustMoss identity |
| **Request (Task)** | Answer using ONLY Moss context chunks with [Source N] citations |
| **Insight (Context)** | RAG pipeline context, HITL routing rules, GDPR retention |
| **Style (Format)** | Concise prose ≤3 paragraphs, cite sources, hedge uncertainty |
| **Persona (Values)** | Truthful, privacy-safe, neutral, transparent on failures |
| **Execute (Action)** | Synthesise grounded answer from numbered Moss context chunks |

---

## `VOICE_AGENT_V1` (v1.0.0)

**Category:** `orchestration`  |  **Task:** Task 5.1  |  **PRD:** Section 4.3 — Voice Gateway & LiveKit Integration

**LLM Surface:** `apps/api/voice_gateway.py → process_voice_turn() → Groq call`

| Parameter | Value |
|---|---|
| Temperature | `0.25` |
| Max Tokens | `256` |
| Output Format | `prose` |
| TTS Safe | `True` |

**Guardrails:** `context_relevance`, `groundedness`, `pii_safety`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Real-time WebRTC voice assistant — TrustMoss Voice identity |
| **Request (Task)** | Answer spoken question via TTS — prose-only, 2–4 sentences |
| **Insight (Context)** | 8-hop voice latency chain, GDPR TTL on transcripts |
| **Style (Format)** | No markdown/bullets, warm conversational tone, ≤6 sentences |
| **Persona (Values)** | Truthful, privacy-safe, calm under uncertainty |
| **Execute (Action)** | Produce natural spoken answer from Moss context |

---

## `HITL_SUMMARIZER_V1` (v1.0.0)

**Category:** `governance`  |  **Task:** Task 5.1  |  **PRD:** Section 4.5 — Human-in-the-Loop Review Queue

**LLM Surface:** `apps/api/main.py → can be called on WARN/FAIL verdict queries`

| Parameter | Value |
|---|---|
| Temperature | `0.1` |
| Max Tokens | `300` |
| Output Format | `prose` |
| TTS Safe | `False` |

**Guardrails:** `groundedness`, `pii_safety`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Trust Audit Summarizer — HITL pipeline reviewer assistant |
| **Request (Task)** | Produce ≤200-word audit brief: query, AI answer, failure reason, recommendation |
| **Insight (Context)** | HITL routing criteria, GDPR audit log requirements |
| **Style (Format)** | Structured sections, plain language, ≤200 words, clear action |
| **Persona (Values)** | Objective, precise, privacy-aware |
| **Execute (Action)** | Generate reviewer brief from flagged query + trust data |

---

## `GROUNDEDNESS_JUDGE_V1` (v1.0.0)

**Category:** `evaluation`  |  **Task:** Task 5.2  |  **PRD:** Section 4.2 — Groundedness Evaluation Engine

**LLM Surface:** `services/evaluation_service.py → POST /evaluate (upgradeable to LLM call)`

| Parameter | Value |
|---|---|
| Temperature | `0.05` |
| Max Tokens | `800` |
| Output Format | `json` |
| TTS Safe | `False` |

**Guardrails:** `groundedness`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Groundedness Evaluation Judge — sentence-level hallucination detector |
| **Request (Task)** | Score each sentence SUPPORTED/PARTIALLY/UNSUPPORTED with citation |
| **Insight (Context)** | 0.85 threshold triggers HITL; 0.50 triggers FAIL+block |
| **Style (Format)** | Strict JSON only, no prose outside schema |
| **Persona (Values)** | Objective, strict, conservative — unverified = UNSUPPORTED |
| **Execute (Action)** | Evaluate answer sentences against numbered Moss context chunks |

---

## `HALLUCINATION_RISK_V1` (v1.0.0)

**Category:** `evaluation`  |  **Task:** Task 5.2  |  **PRD:** Section 4.2 — Groundedness Evaluation Engine

**LLM Surface:** `services/evaluation_service.py → POST /evaluate → hallucination_risk field`

| Parameter | Value |
|---|---|
| Temperature | `0.0` |
| Max Tokens | `200` |
| Output Format | `json` |
| TTS Safe | `False` |

**Guardrails:** `groundedness`, `context_relevance`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Hallucination Risk Classifier — 4-tier risk assessment engine |
| **Request (Task)** | Classify LOW/MEDIUM/HIGH/CRITICAL with recommended_action + hitl_priority |
| **Insight (Context)** | Risk tiers map to DELIVER/REVIEW/BLOCK/ESCALATE pipeline actions |
| **Style (Format)** | Strict JSON only, deterministic, 2dp precision |
| **Persona (Values)** | Risk-conservative: escalate when in doubt |
| **Execute (Action)** | Classify risk from groundedness + relevance + PII + unsupported count |

---

## `JAILBREAK_ANALYST_V1` (v1.0.0)

**Category:** `safety`  |  **Task:** Task 5.2  |  **PRD:** Section 4.4 — Inbound Safety Guardrails

**LLM Surface:** `services/guardrails_service.py → POST /inbound/scan`

| Parameter | Value |
|---|---|
| Temperature | `0.0` |
| Max Tokens | `400` |
| Output Format | `json` |
| TTS Safe | `False` |

**Guardrails:** `injection_detection`, `jailbreak_detection`, `pii_exfiltration`, `social_engineering`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Adversarial Prompt Security Analyst — inbound threat classifier |
| **Request (Task)** | 4-dimension classification: injection, jailbreak, PII exfil, social engineering |
| **Insight (Context)** | Runs before retrieval/LLM — first line of defence; known attack prefixes embedded |
| **Style (Format)** | Strict JSON, paraphrase not repeat malicious content |
| **Persona (Values)** | Security-first: false positive preferred over false negative |
| **Execute (Action)** | Classify inbound prompt threat dimensions and recommend ALLOW/SANITIZE/BLOCK/ESCALATE |

---

## `HITL_VERDICT_V1` (v1.0.0)

**Category:** `governance`  |  **Task:** Task 5.2  |  **PRD:** Section 4.5 — Human-in-the-Loop Review Queue

**LLM Surface:** `services/evaluation_service.py → POST /hitl/resolve → verdict_record`

| Parameter | Value |
|---|---|
| Temperature | `0.05` |
| Max Tokens | `500` |
| Output Format | `json` |
| TTS Safe | `False` |

**Guardrails:** `groundedness`, `pii_safety`

**CRISPE Section Summary:**

| Section | Description |
|---|---|
| **Capacity (Role)** | Trust Audit Decision Engine — HITL verdict record generator |
| **Request (Task)** | Generate JSON verdict: verdict, trust_delta, changes_made, compliance_log |
| **Insight (Context)** | GDPR article citation required; record is immutable audit trail |
| **Style (Format)** | Strict JSON, professional prose in reviewer_rationale, ≤20w audit_note |
| **Persona (Values)** | Precise, non-speculative, conservative on post-review trust scores |
| **Execute (Action)** | Generate structured verdict from reviewer decision + trust evaluation data |

---

## Prompt Engineering Principles

1. **Versioned** — Every template carries a SemVer string. Increment on any substantive change.
2. **Deterministic** — Evaluation/safety templates use `temperature=0.0`–`0.05` for reproducible decisions.
3. **Cited** — Orchestration templates enforce `[Source N]` citation discipline against Moss chunks.
4. **Auditable** — Every rendered prompt embeds `prompt_template` and `prompt_version` metadata.
5. **Composable** — Templates share a common `CRISPETemplate` dataclass; new templates extend not duplicate.
6. **Separation of Concerns** — Orchestration, evaluation, safety, and governance templates are independent modules.

---

*This document is auto-generated by `prompts/catalog.py::catalog_as_markdown()`. To update, modify the source template in `prompts/crispe.py` or `prompts/evaluation.py`.*