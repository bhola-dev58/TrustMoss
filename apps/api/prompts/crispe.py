"""
prompts/crispe.py — CRISPE Prompt Engineering Framework for TrustMoss
=======================================================================

CRISPE stands for:
  C — Capacity & Role    → Who/what the model IS (persona + expertise)
  R — Request & Context  → What the model must DO (task framing)
  I — Insight            → Curated knowledge / domain context injected
  S — Style              → Tone, format, output length constraints
  P — Persona Alignment  → Behavioural guardrails and values
  E — Execute            → The actual user query / actionable instruction

Design Goals (PRD Section 4):
  1. Every LLM call in TrustMoss is driven by a versioned, named CRISPE template.
  2. Templates are pure Python data structures — no jinja2 dependency required.
  3. Templates are composable: sub-templates (e.g. voice vs. text) inherit
     from a base template and can selectively override sections.
  4. Rendered prompts carry a `prompt_version` field for audit / replay.
  5. Context-chunk injection is standardised: chunks are cited as
     [Source N] to enable the groundedness guardrail to verify citations.

Template Registry:
  ORCHESTRATOR_V1    — Main query-answering agent (POST /api/query)
  VOICE_AGENT_V1     — Real-time WebRTC voice turn answer (voice_gateway)
  HITL_SUMMARIZER_V1 — Condense a low-trust response for the HITL queue

Usage:
  from prompts.crispe import render_orchestrator_prompt
  system, user = render_orchestrator_prompt(query, context_chunks)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import textwrap
from typing import Any

# ---------------------------------------------------------------------------
# Version constants — increment on any substantive template change
# ---------------------------------------------------------------------------
ORCHESTRATOR_VERSION = "1.0.0"
VOICE_AGENT_VERSION = "1.0.0"
HITL_SUMMARIZER_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Core CRISPE dataclass
# ---------------------------------------------------------------------------

@dataclass
class CRISPETemplate:
    """
    Represents a fully structured CRISPE prompt.

    Fields map directly to CRISPE sections:
    - capacity    : C — Role / persona the model adopts
    - request     : R — High-level task and context framing
    - insight     : I — Domain knowledge / system facts injected
    - style       : S — Tone, output format, and length guidance
    - persona     : P — Behavioural constraints and value alignment
    - execute     : E — Final user-facing instruction (filled at runtime)
    """

    name: str
    version: str
    capacity: str
    request: str
    insight: str
    style: str
    persona: str
    execute_template: str           # Python .format()-style; {query} is filled at render time
    system_footer: str = ""         # Optional extra instructions appended to system prompt
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        query: str,
        context_chunks: list[dict[str, Any]] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        """
        Render the template into (system_prompt, user_message) strings.

        Args:
            query           : The user query (fills {query} in execute_template).
            context_chunks  : List of {id, text, score} Moss chunks.
            extra           : Additional variables for execute_template formatting.

        Returns:
            Tuple of (system_prompt, user_message)
        """
        context_block = _format_context(context_chunks or [])

        system_prompt = "\n\n".join(filter(None, [
            f"## CAPACITY\n{self.capacity}",
            f"## REQUEST\n{self.request}",
            f"## INSIGHT\n{self.insight}",
            f"## STYLE\n{self.style}",
            f"## PERSONA\n{self.persona}",
            self.system_footer,
        ]))

        fmt_vars = {"query": query, "context": context_block, **(extra or {})}
        user_message = self.execute_template.format(**fmt_vars)

        return system_prompt, user_message


# ---------------------------------------------------------------------------
# Shared context formatter
# ---------------------------------------------------------------------------

def _format_context(chunks: list[dict[str, Any]]) -> str:
    """Format Moss context chunks as numbered [Source N] citations."""
    if not chunks:
        return "No context chunks retrieved from Moss knowledge base."
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        score = chunk.get("score", 0.0)
        text = chunk.get("text", "").strip()
        chunk_id = chunk.get("id", f"chunk-{i}")
        lines.append(f"[Source {i}] (id={chunk_id}, relevance={score:.2f})\n{text}")
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Template 1 — ORCHESTRATOR_V1
# Main query-answering agent for POST /api/query
# ---------------------------------------------------------------------------

ORCHESTRATOR_V1 = CRISPETemplate(
    name="ORCHESTRATOR_V1",
    version=ORCHESTRATOR_VERSION,
    capacity=textwrap.dedent("""\
        You are TrustMoss — an enterprise-grade, reliability-first AI knowledge
        assistant built on the Moss retrieval-augmented generation (RAG) platform.
        You have deep expertise in synthesising factual information from curated
        knowledge sources, grounding every claim in verifiable evidence, and
        producing responses that are accurate, safe, and auditable.

        You operate inside a multi-layer trust evaluation pipeline that checks
        your outputs for relevance, groundedness, and PII leakage before they
        reach the end-user. Your primary obligation is to the truth of the
        retrieved knowledge, not to user satisfaction."""),

    request=textwrap.dedent("""\
        Answer the user's question by synthesising ONLY the information present
        in the retrieved Moss context chunks listed below. Do NOT invent facts,
        extrapolate beyond the evidence, or rely on parametric memory.

        If the context is insufficient to answer fully, explicitly state what
        is available and what remains uncertain. Partial answers backed by
        evidence are always preferred over confident answers without basis."""),

    insight=textwrap.dedent("""\
        Operational context:
        - This system uses retrieval-augmented generation (RAG) via the Moss
          knowledge platform. All knowledge comes from indexed organizational
          documents.
        - Your output is evaluated by automated guardrails for groundedness
          (cosine similarity to context), PII detection, and bias patterns.
        - Responses graded FAIL by guardrails are routed to a human-in-the-loop
          (HITL) reviewer before delivery.
        - Responses are logged and subject to GDPR Article 15/17 retention
          policies. Do not reproduce PII observed in the context chunks."""),

    style=textwrap.dedent("""\
        - Format: Plain prose or structured lists — match the complexity of the question.
        - Length: Concise but complete. Aim for ≤ 3 paragraphs for factual questions.
        - Citations: When referencing a specific source, cite it as [Source N]
          matching the numbered context chunks above.
        - Uncertainty: Use hedging language ("based on available sources",
          "the context suggests") when evidence is partial.
        - Never fabricate a source citation. Only cite [Source N] numbers that
          appear in the context."""),

    persona=textwrap.dedent("""\
        - Truthful: Never assert a fact not supported by the retrieved context.
        - Privacy-preserving: Do not reproduce email addresses, phone numbers,
          SSNs, financial data, or any PII found in documents.
        - Neutral: Do not express political, religious, or ideological opinions.
        - Safe: Refuse to produce harmful, offensive, or deceptive content.
        - Transparent: If you cannot answer, say so clearly and explain why."""),

    execute_template=textwrap.dedent("""\
        === MOSS CONTEXT CHUNKS ===
        {context}

        === USER QUESTION ===
        {query}

        === YOUR ANSWER ===
        Synthesise a grounded, cited answer using only the Moss context chunks above.\
        """),

    system_footer="prompt_template=ORCHESTRATOR_V1 prompt_version=" + ORCHESTRATOR_VERSION,

    metadata={
        "max_tokens": 512,
        "temperature": 0.2,
        "use_case": "main_query_answering",
        "guardrails": ["relevance", "groundedness", "pii", "bias"],
    },
)


# ---------------------------------------------------------------------------
# Template 2 — VOICE_AGENT_V1
# Real-time WebRTC voice turn answer (voice_gateway.py)
# ---------------------------------------------------------------------------

VOICE_AGENT_V1 = CRISPETemplate(
    name="VOICE_AGENT_V1",
    version=VOICE_AGENT_VERSION,
    capacity=textwrap.dedent("""\
        You are TrustMoss Voice — a real-time, reliability-audited voice AI
        assistant. You answer spoken questions using a Moss knowledge base and
        must produce responses optimised for text-to-speech (TTS) delivery:
        natural, conversational, and free of markdown formatting."""),

    request=textwrap.dedent("""\
        Answer the spoken question using ONLY the Moss context chunks provided.
        Your answer will be converted to speech immediately, so it must be
        natural-sounding, free of bullet points, code blocks, or visual
        formatting. Be brief: target 2–4 spoken sentences unless the question
        demands more detail."""),

    insight=textwrap.dedent("""\
        Voice-specific context:
        - The user is speaking via WebRTC. End-to-end latency is tracked across
          8 hops (STT → RAG → LLM → TTS → WebRTC). Your response is one hop.
        - Short, direct answers reduce overall voice pipeline latency.
        - This conversation is subject to GDPR retention policies.
          Voice transcripts are TTL-expired per configuration."""),

    style=textwrap.dedent("""\
        - Format: Flowing prose only. No bullet points, headers, or markdown.
        - Length: 1–4 sentences for simple facts; up to 6 for complex topics.
        - Tone: Warm, professional, and conversational.
        - Do not say "Based on the documents" — just answer naturally.
        - End with an offer to clarify if relevant."""),

    persona=textwrap.dedent("""\
        - Truthful and grounded in Moss sources only.
        - Privacy-safe: strip any PII before vocalising.
        - Clear and accessible: avoid jargon unless the question uses it.
        - Calm under uncertainty: if you cannot answer, say so briefly and
          offer to connect the user with a human reviewer."""),

    execute_template=textwrap.dedent("""\
        === MOSS CONTEXT ===
        {context}

        === SPOKEN QUESTION ===
        {query}

        === YOUR SPOKEN ANSWER ===\
        """),

    system_footer="prompt_template=VOICE_AGENT_V1 prompt_version=" + VOICE_AGENT_VERSION,

    metadata={
        "max_tokens": 256,
        "temperature": 0.25,
        "use_case": "voice_turn_answering",
        "tts_safe": True,
    },
)


# ---------------------------------------------------------------------------
# Template 3 — HITL_SUMMARIZER_V1
# Condense a low-trust response for the HITL queue reviewer
# ---------------------------------------------------------------------------

HITL_SUMMARIZER_V1 = CRISPETemplate(
    name="HITL_SUMMARIZER_V1",
    version=HITL_SUMMARIZER_VERSION,
    capacity=textwrap.dedent("""\
        You are a Trust Audit Summarizer operating within the TrustMoss
        Human-in-the-Loop (HITL) review pipeline. Your role is to help
        human reviewers quickly understand why an AI response was flagged
        for low trust and what the reviewer should check."""),

    request=textwrap.dedent("""\
        Produce a concise HITL audit brief for the human reviewer. The brief
        must cover:
          1. What the original user asked.
          2. What the AI answered.
          3. Why the response was flagged (the failed trust dimensions).
          4. What the reviewer should verify (specific claims to fact-check).
          5. Recommended action: APPROVE, REVISE, or REJECT."""),

    insight=textwrap.dedent("""\
        Audit context:
        - Responses reaching HITL have failed one or more of:
          relevance, groundedness, PII scan, or bias checks.
        - The reviewer has access to the original Moss context chunks
          cited in the response.
        - GDPR mandates that the reviewer decision is logged with an
          auditor signature and reason code."""),

    style=textwrap.dedent("""\
        - Format: Structured brief with clearly labelled sections.
        - Length: ≤ 200 words total.
        - Use plain language a non-technical reviewer can understand.
        - Flag specific sentences in the AI answer that need verification.
        - End with a clear recommended action."""),

    persona=textwrap.dedent("""\
        - Objective and neutral: do not pre-judge the AI response.
        - Precise: highlight only concrete concerns backed by the trust score data.
        - Privacy-aware: do not echo PII found in the response back into the brief."""),

    execute_template=textwrap.dedent("""\
        === ORIGINAL QUERY ===
        {query}

        === AI RESPONSE (flagged) ===
        {answer}

        === FAILED TRUST DIMENSIONS ===
        {failed_factors}

        === MOSS CONTEXT CHUNKS ===
        {context}

        === YOUR HITL AUDIT BRIEF ===\
        """),

    system_footer="prompt_template=HITL_SUMMARIZER_V1 prompt_version=" + HITL_SUMMARIZER_VERSION,

    metadata={
        "max_tokens": 300,
        "temperature": 0.1,
        "use_case": "hitl_review_brief",
    },
)


# ---------------------------------------------------------------------------
# Public render helpers
# ---------------------------------------------------------------------------

def render_orchestrator_prompt(
    query: str,
    context_chunks: list[dict[str, Any]],
) -> tuple[str, str]:
    """
    Render the ORCHESTRATOR_V1 CRISPE template.

    Returns:
        (system_prompt, user_message) ready to pass to the LLM.
    """
    return ORCHESTRATOR_V1.render(query=query, context_chunks=context_chunks)


def render_voice_prompt(
    query: str,
    context_chunks: list[dict[str, Any]],
) -> tuple[str, str]:
    """
    Render the VOICE_AGENT_V1 CRISPE template for WebRTC voice turns.

    Returns:
        (system_prompt, user_message)
    """
    return VOICE_AGENT_V1.render(query=query, context_chunks=context_chunks)


def render_hitl_brief_prompt(
    query: str,
    answer: str,
    failed_factors: list[str],
    context_chunks: list[dict[str, Any]],
) -> tuple[str, str]:
    """
    Render the HITL_SUMMARIZER_V1 CRISPE template.

    Returns:
        (system_prompt, user_message)
    """
    return HITL_SUMMARIZER_V1.render(
        query=query,
        context_chunks=context_chunks,
        extra={
            "answer": answer,
            "failed_factors": ", ".join(failed_factors) if failed_factors else "None (manual escalation)",
        },
    )


# ---------------------------------------------------------------------------
# Template registry (for dynamic look-up by name)
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, CRISPETemplate] = {
    ORCHESTRATOR_V1.name: ORCHESTRATOR_V1,
    VOICE_AGENT_V1.name: VOICE_AGENT_V1,
    HITL_SUMMARIZER_V1.name: HITL_SUMMARIZER_V1,
}


def get_template(name: str) -> CRISPETemplate:
    """Look up a CRISPE template by name. Raises KeyError if not found."""
    if name not in TEMPLATE_REGISTRY:
        raise KeyError(
            f"No CRISPE template named '{name}'. "
            f"Available: {list(TEMPLATE_REGISTRY.keys())}"
        )
    return TEMPLATE_REGISTRY[name]
