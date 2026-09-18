"""
prompts/catalog.py — Prompt Catalog Module for TrustMoss (Task 5.3)
=====================================================================

Purpose:
  Provides a machine-readable, auto-syncing catalog of every CRISPE prompt
  template registered in TrustMoss. Drives:

    1. GET /api/prompts/catalog        — Full catalog listing for the UI/PRD
    2. GET /api/prompts/catalog/{name} — Deep-link to a single template spec
    3. PROMPT_CATALOG.md              — Auto-generated human-readable PRD doc

Catalog fields per template:
  - name             : Unique template identifier
  - version          : SemVer string
  - category         : orchestration | evaluation | safety | governance
  - use_case         : Free-text description of where it is used
  - llm_surface      : Which service/endpoint renders this template
  - temperature      : LLM sampling temperature
  - max_tokens       : Maximum output tokens
  - output_format    : prose | json
  - guardrails       : List of guardrail dimensions this template supports
  - prd_section      : PRD section reference (e.g. "Section 4.2")
  - crispe_summary   : One-line description of each C/R/I/S/P/E section
  - added_in_task    : Which task added this template (for traceability)

Design:
  - catalog() is the single source of truth — it reads TEMPLATE_REGISTRY live.
  - No duplication: template metadata is owned by the CRISPETemplate dataclass.
  - catalog_as_markdown() auto-generates the PRD-embeddable doc from catalog().
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Import both template modules so they register themselves
from prompts.crispe import TEMPLATE_REGISTRY, CRISPETemplate

# ---------------------------------------------------------------------------
# Category & surface metadata (enriches the raw template metadata)
# ---------------------------------------------------------------------------

_TEMPLATE_ENRICHMENT: dict[str, dict[str, Any]] = {
    "ORCHESTRATOR_V1": {
        "category": "orchestration",
        "llm_surface": "apps/api/main.py → POST /api/query → call_llm()",
        "guardrails": ["context_relevance", "groundedness", "pii_safety", "bias_toxicity"],
        "prd_section": "Section 4.1 — Agent Orchestration",
        "added_in_task": "Task 5.1",
        "crispe_summary": {
            "C": "Enterprise RAG knowledge assistant — TrustMoss identity",
            "R": "Answer using ONLY Moss context chunks with [Source N] citations",
            "I": "RAG pipeline context, HITL routing rules, GDPR retention",
            "S": "Concise prose ≤3 paragraphs, cite sources, hedge uncertainty",
            "P": "Truthful, privacy-safe, neutral, transparent on failures",
            "E": "Synthesise grounded answer from numbered Moss context chunks",
        },
    },
    "VOICE_AGENT_V1": {
        "category": "orchestration",
        "llm_surface": "apps/api/voice_gateway.py → process_voice_turn() → Groq call",
        "guardrails": ["context_relevance", "groundedness", "pii_safety"],
        "prd_section": "Section 4.3 — Voice Gateway & LiveKit Integration",
        "added_in_task": "Task 5.1",
        "crispe_summary": {
            "C": "Real-time WebRTC voice assistant — TrustMoss Voice identity",
            "R": "Answer spoken question via TTS — prose-only, 2–4 sentences",
            "I": "8-hop voice latency chain, GDPR TTL on transcripts",
            "S": "No markdown/bullets, warm conversational tone, ≤6 sentences",
            "P": "Truthful, privacy-safe, calm under uncertainty",
            "E": "Produce natural spoken answer from Moss context",
        },
    },
    "HITL_SUMMARIZER_V1": {
        "category": "governance",
        "llm_surface": "apps/api/main.py → can be called on WARN/FAIL verdict queries",
        "guardrails": ["groundedness", "pii_safety"],
        "prd_section": "Section 4.5 — Human-in-the-Loop Review Queue",
        "added_in_task": "Task 5.1",
        "crispe_summary": {
            "C": "Trust Audit Summarizer — HITL pipeline reviewer assistant",
            "R": "Produce ≤200-word audit brief: query, AI answer, failure reason, recommendation",
            "I": "HITL routing criteria, GDPR audit log requirements",
            "S": "Structured sections, plain language, ≤200 words, clear action",
            "P": "Objective, precise, privacy-aware",
            "E": "Generate reviewer brief from flagged query + trust data",
        },
    },
    "GROUNDEDNESS_JUDGE_V1": {
        "category": "evaluation",
        "llm_surface": "services/evaluation_service.py → POST /evaluate (upgradeable to LLM call)",
        "guardrails": ["groundedness"],
        "prd_section": "Section 4.2 — Groundedness Evaluation Engine",
        "added_in_task": "Task 5.2",
        "crispe_summary": {
            "C": "Groundedness Evaluation Judge — sentence-level hallucination detector",
            "R": "Score each sentence SUPPORTED/PARTIALLY/UNSUPPORTED with citation",
            "I": "0.85 threshold triggers HITL; 0.50 triggers FAIL+block",
            "S": "Strict JSON only, no prose outside schema",
            "P": "Objective, strict, conservative — unverified = UNSUPPORTED",
            "E": "Evaluate answer sentences against numbered Moss context chunks",
        },
    },
    "HALLUCINATION_RISK_V1": {
        "category": "evaluation",
        "llm_surface": "services/evaluation_service.py → POST /evaluate → hallucination_risk field",
        "guardrails": ["groundedness", "context_relevance"],
        "prd_section": "Section 4.2 — Groundedness Evaluation Engine",
        "added_in_task": "Task 5.2",
        "crispe_summary": {
            "C": "Hallucination Risk Classifier — 4-tier risk assessment engine",
            "R": "Classify LOW/MEDIUM/HIGH/CRITICAL with recommended_action + hitl_priority",
            "I": "Risk tiers map to DELIVER/REVIEW/BLOCK/ESCALATE pipeline actions",
            "S": "Strict JSON only, deterministic, 2dp precision",
            "P": "Risk-conservative: escalate when in doubt",
            "E": "Classify risk from groundedness + relevance + PII + unsupported count",
        },
    },
    "JAILBREAK_ANALYST_V1": {
        "category": "safety",
        "llm_surface": "services/guardrails_service.py → POST /inbound/scan",
        "guardrails": ["injection_detection", "jailbreak_detection", "pii_exfiltration", "social_engineering"],
        "prd_section": "Section 4.4 — Inbound Safety Guardrails",
        "added_in_task": "Task 5.2",
        "crispe_summary": {
            "C": "Adversarial Prompt Security Analyst — inbound threat classifier",
            "R": "4-dimension classification: injection, jailbreak, PII exfil, social engineering",
            "I": "Runs before retrieval/LLM — first line of defence; known attack prefixes embedded",
            "S": "Strict JSON, paraphrase not repeat malicious content",
            "P": "Security-first: false positive preferred over false negative",
            "E": "Classify inbound prompt threat dimensions and recommend ALLOW/SANITIZE/BLOCK/ESCALATE",
        },
    },
    "HITL_VERDICT_V1": {
        "category": "governance",
        "llm_surface": "services/evaluation_service.py → POST /hitl/resolve → verdict_record",
        "guardrails": ["groundedness", "pii_safety"],
        "prd_section": "Section 4.5 — Human-in-the-Loop Review Queue",
        "added_in_task": "Task 5.2",
        "crispe_summary": {
            "C": "Trust Audit Decision Engine — HITL verdict record generator",
            "R": "Generate JSON verdict: verdict, trust_delta, changes_made, compliance_log",
            "I": "GDPR article citation required; record is immutable audit trail",
            "S": "Strict JSON, professional prose in reviewer_rationale, ≤20w audit_note",
            "P": "Precise, non-speculative, conservative on post-review trust scores",
            "E": "Generate structured verdict from reviewer decision + trust evaluation data",
        },
    },
}

# ---------------------------------------------------------------------------
# Core catalog builder
# ---------------------------------------------------------------------------

def build_catalog_entry(template: CRISPETemplate) -> dict[str, Any]:
    """Build a single catalog entry by merging template metadata with enrichment data."""
    enrichment = _TEMPLATE_ENRICHMENT.get(template.name, {})
    meta = template.metadata

    return {
        "name": template.name,
        "version": template.version,
        "category": enrichment.get("category", "uncategorized"),
        "use_case": meta.get("use_case", ""),
        "llm_surface": enrichment.get("llm_surface", ""),
        "temperature": meta.get("temperature", 0.2),
        "max_tokens": meta.get("max_tokens", 512),
        "output_format": meta.get("output_format", "prose"),
        "guardrails": enrichment.get("guardrails", []),
        "prd_section": enrichment.get("prd_section", ""),
        "crispe_summary": enrichment.get("crispe_summary", {}),
        "added_in_task": enrichment.get("added_in_task", ""),
        "tts_safe": meta.get("tts_safe", False),
    }


def catalog() -> dict[str, Any]:
    """
    Returns the full CRISPE Prompt Catalog as a dict.
    Auto-syncs with TEMPLATE_REGISTRY — no manual maintenance required.
    """
    entries = [build_catalog_entry(t) for t in TEMPLATE_REGISTRY.values()]

    # Group by category for structured output
    by_category: dict[str, list] = {}
    for entry in entries:
        cat = entry["category"]
        by_category.setdefault(cat, []).append(entry)

    return {
        "catalog_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_templates": len(entries),
        "categories": list(by_category.keys()),
        "templates": entries,
        "by_category": by_category,
        "summary": {
            cat: len(items)
            for cat, items in by_category.items()
        },
    }


def get_catalog_entry(template_name: str) -> dict[str, Any]:
    """Returns the catalog entry for a single named template. Raises KeyError if not found."""
    if template_name not in TEMPLATE_REGISTRY:
        raise KeyError(
            f"Template '{template_name}' not found in TEMPLATE_REGISTRY. "
            f"Available: {list(TEMPLATE_REGISTRY.keys())}"
        )
    return build_catalog_entry(TEMPLATE_REGISTRY[template_name])


# ---------------------------------------------------------------------------
# PRD-embeddable Markdown generator
# ---------------------------------------------------------------------------

def catalog_as_markdown() -> str:
    """
    Auto-generates the PROMPT_CATALOG.md PRD document from the live registry.
    Called at startup to write docs/PROMPT_CATALOG.md.
    """
    data = catalog()
    lines = [
        "# TrustMoss CRISPE Prompt Catalog",
        "",
        "> **Auto-generated from `TEMPLATE_REGISTRY`** — do not edit manually.",
        f"> Generated: {data['generated_at']}  |  Catalog Version: {data['catalog_version']}",
        "",
        "## Overview",
        "",
        f"TrustMoss uses **{data['total_templates']} versioned CRISPE prompt templates** "
        "to govern every LLM interaction across the platform.",
        "All templates are named, versioned (SemVer), and registered in a shared "
        "`TEMPLATE_REGISTRY` for auditability and replay.",
        "",
        "| Category | Count |",
        "|---|---|",
    ]
    for cat, count in data["summary"].items():
        lines.append(f"| `{cat}` | {count} |")

    lines += ["", "---", ""]

    # Detail section per template
    for entry in data["templates"]:
        lines += [
            f"## `{entry['name']}` (v{entry['version']})",
            "",
            f"**Category:** `{entry['category']}`  |  "
            f"**Task:** {entry['added_in_task']}  |  "
            f"**PRD:** {entry['prd_section']}",
            "",
            f"**LLM Surface:** `{entry['llm_surface']}`",
            "",
            "| Parameter | Value |",
            "|---|---|",
            f"| Temperature | `{entry['temperature']}` |",
            f"| Max Tokens | `{entry['max_tokens']}` |",
            f"| Output Format | `{entry['output_format']}` |",
            f"| TTS Safe | `{entry['tts_safe']}` |",
            "",
        ]

        if entry["guardrails"]:
            lines.append(f"**Guardrails:** {', '.join(f'`{g}`' for g in entry['guardrails'])}")
            lines.append("")

        if entry["crispe_summary"]:
            lines += [
                "**CRISPE Section Summary:**",
                "",
                "| Section | Description |",
                "|---|---|",
            ]
            labels = {
                "C": "Capacity (Role)",
                "R": "Request (Task)",
                "I": "Insight (Context)",
                "S": "Style (Format)",
                "P": "Persona (Values)",
                "E": "Execute (Action)",
            }
            for key, label in labels.items():
                desc = entry["crispe_summary"].get(key, "—")
                lines.append(f"| **{label}** | {desc} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## Prompt Engineering Principles",
        "",
        "1. **Versioned** — Every template carries a SemVer string. Increment on any substantive change.",
        "2. **Deterministic** — Evaluation/safety templates use `temperature=0.0`–`0.05` for reproducible decisions.",
        "3. **Cited** — Orchestration templates enforce `[Source N]` citation discipline against Moss chunks.",
        "4. **Auditable** — Every rendered prompt embeds `prompt_template` and `prompt_version` metadata.",
        "5. **Composable** — Templates share a common `CRISPETemplate` dataclass; new templates extend not duplicate.",
        "6. **Separation of Concerns** — Orchestration, evaluation, safety, and governance templates are independent modules.",
        "",
        "---",
        "",
        "*This document is auto-generated by `prompts/catalog.py::catalog_as_markdown()`. "
        "To update, modify the source template in `prompts/crispe.py` or `prompts/evaluation.py`.*",
    ]

    return "\n".join(lines)
