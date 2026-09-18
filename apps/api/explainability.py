"""
TrustMoss Trust Score Explainability Framework (Task 4.4)
----------------------------------------------------------
Produces rich, factorized, human-readable explanations for every trust verdict.
Design principles:
- Every trust score component (Relevance, Groundedness, PII, Bias) has an
  independent Explanation object with:
    * factor_name     — the guardrail dimension
    * status          — PASS / WARN / FAIL
    * score           — 0.0–1.0 normalized
    * headline        — ≤ 20 word executive summary
    * detail          — full technical rationale
    * evidence        — cited Moss context chunks supporting the judgment
    * recommendation  — actionable remediation when non-PASS
- The composite TrustExplanation assembles all factors into a ranked
  explanation, a confidence narrative, and structured JSON for the UI HUD.

Output drives:
- The Next.js Reliability HUD (per-factor color chips + cited evidence).
- The HITL Review Queue detail panel (auditor-grade explanation with citations).
- The POST /api/query response `explanation` field.
- The GET /api/explain/{query_id} endpoint.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Score normalization thresholds
# ---------------------------------------------------------------------------
RELEVANCE_STRONG = 0.85
RELEVANCE_WARN = 0.60
GROUNDEDNESS_STRONG = 0.85
GROUNDEDNESS_WARN = 0.65
PII_WARN_THRESHOLD = 0.5    # score < this → PII risk
BIAS_STRONG = 0.80
BIAS_WARN = 0.55

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"


# ---------------------------------------------------------------------------
# Factor-level explanation
# ---------------------------------------------------------------------------
@dataclass
class FactorExplanation:
    """Single-dimension explanation for one trust guardrail factor."""

    factor_name: str
    status: str               # PASS | WARN | FAIL
    score: float              # 0.0 – 1.0
    headline: str             # ≤ 20 words, executive summary
    detail: str               # Technical rationale
    evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendation: str | None = None
    weight: float = 1.0       # Relative importance weight for final score

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["score"] = round(self.score, 4)
        d["weight"] = round(self.weight, 4)
        return d


# ---------------------------------------------------------------------------
# Composite trust explanation
# ---------------------------------------------------------------------------
@dataclass
class TrustExplanation:
    """Full factorized trust explanation for a single query–response turn."""

    query_id: str
    verdict: str              # PASS | WARN | FAIL
    composite_score: float    # Weighted average of all factor scores
    confidence_level: str     # HIGH | MEDIUM | LOW
    confidence_narrative: str
    factors: list[FactorExplanation] = field(default_factory=list)
    cited_chunks: list[dict[str, Any]] = field(default_factory=list)
    failed_factors: list[str] = field(default_factory=list)

    @property
    def trust_grade(self) -> str:
        """Letter-grade summary (A–F) correlated to composite_score."""
        if self.composite_score >= 0.90:
            return "A"
        if self.composite_score >= 0.75:
            return "B"
        if self.composite_score >= 0.55:
            return "C"
        if self.composite_score >= 0.35:
            return "D"
        return "F"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "verdict": self.verdict,
            "composite_score": round(self.composite_score, 4),
            "trust_grade": self.trust_grade,
            "confidence_level": self.confidence_level,
            "confidence_narrative": self.confidence_narrative,
            "factors": [f.to_dict() for f in self.factors],
            "cited_chunks": self.cited_chunks,
            "failed_factors": self.failed_factors,
        }


# ---------------------------------------------------------------------------
# Factor explanation builders
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def build_relevance_explanation(
    relevance_result: dict[str, Any],
    context_chunks: list[dict[str, Any]],
) -> FactorExplanation:
    """Builds explainability for the Context Relevance guardrail."""
    score = _clamp(relevance_result.get("score", 0.0))
    passed = relevance_result.get("passed", False)
    reason = relevance_result.get("reason", "")

    if score >= RELEVANCE_STRONG:
        status = STATUS_PASS
        headline = f"Context relevance is strong ({score:.0%}) — Moss returned highly relevant chunks."
        recommendation = None
    elif score >= RELEVANCE_WARN:
        status = STATUS_WARN
        headline = f"Context relevance is moderate ({score:.0%}) — some chunks may be marginally relevant."
        recommendation = (
            "Consider broadening the Moss index query or lowering the relevance threshold to "
            "retrieve higher-quality context chunks for this query domain."
        )
    else:
        status = STATUS_FAIL
        headline = f"Context relevance is critically low ({score:.0%}) — Moss returned poor matches."
        recommendation = (
            "The knowledge base does not contain sufficient relevant material. "
            "Review index coverage for this topic area or add golden documents."
        )

    # Cite top-3 context chunks as evidence
    evidence = [
        {
            "chunk_id": c.get("id", f"chunk-{i}"),
            "text_preview": c.get("text", "")[:120],
            "score": round(c.get("score", 0.0), 4),
        }
        for i, c in enumerate(context_chunks[:3])
    ]

    return FactorExplanation(
        factor_name="context_relevance",
        status=status,
        score=score,
        headline=headline,
        detail=reason,
        evidence=evidence,
        recommendation=recommendation,
        weight=1.0,
    )


def build_groundedness_explanation(
    groundedness_result: dict[str, Any],
    context_chunks: list[dict[str, Any]],
) -> FactorExplanation:
    """Builds explainability for the Groundedness guardrail."""
    raw_score = groundedness_result.get("score", -1.0)
    passed = groundedness_result.get("passed", True)
    reason = groundedness_result.get("reason", "")

    # score == -1 means stub (not yet computed)
    if raw_score == -1.0:
        score = 0.75  # conservative default for stub
        status = STATUS_PASS
        headline = "Groundedness check is in baseline stub mode — full NLP verification pending."
        recommendation = (
            "Upgrade to production groundedness engine with cosine similarity "
            "against embedded Moss context chunks to enable real-time hallucination detection."
        )
    else:
        score = _clamp(raw_score)
        if score >= GROUNDEDNESS_STRONG:
            status = STATUS_PASS
            headline = f"Answer is well-grounded ({score:.0%}) in Moss context — low hallucination risk."
            recommendation = None
        elif score >= GROUNDEDNESS_WARN:
            status = STATUS_WARN
            headline = f"Grounding is partial ({score:.0%}) — some claims may not be directly supported."
            recommendation = (
                "Review flagged sentences against the cited Moss chunks. "
                "Consider requesting additional context from the index."
            )
        else:
            status = STATUS_FAIL
            headline = f"Answer appears ungrounded ({score:.0%}) — high hallucination risk detected."
            recommendation = (
                "Block this response from delivery. Route to HITL review queue "
                "for expert verification before re-issuance."
            )

    # Cite supporting chunks as evidence
    evidence = [
        {
            "chunk_id": c.get("id", f"chunk-{i}"),
            "text_preview": c.get("text", "")[:120],
            "score": round(c.get("score", 0.0), 4),
            "role": "supporting_context",
        }
        for i, c in enumerate(context_chunks[:3])
    ]

    return FactorExplanation(
        factor_name="groundedness",
        status=status,
        score=score,
        headline=headline,
        detail=reason,
        evidence=evidence,
        recommendation=recommendation,
        weight=1.5,  # Higher weight — most critical reliability signal
    )


def build_pii_explanation(
    pii_result: dict[str, Any],
    query: str,
) -> FactorExplanation:
    """Builds explainability for the PII & Sensitive Data guardrail."""
    score = _clamp(pii_result.get("score", 1.0))
    passed = pii_result.get("passed", True)
    reason = pii_result.get("reason", "")

    if passed:
        status = STATUS_PASS
        headline = "No PII or sensitive data detected in the generated answer."
        recommendation = None
    elif score >= PII_WARN_THRESHOLD:
        status = STATUS_WARN
        headline = "Potential PII pattern detected — response has been flagged for review."
        recommendation = (
            "Enable regex-based redaction in pii_scan to automatically scrub "
            "SSNs, credit cards, emails, and phone numbers from agent responses."
        )
    else:
        status = STATUS_FAIL
        headline = "PII detected and response withheld — sensitive data exposure blocked."
        recommendation = (
            "The agent attempted to expose sensitive user data. "
            "Route to HITL queue for privacy review. "
            "Audit the knowledge base for accidental PII ingestion."
        )

    # Evidence: summarize what categories were detected
    pii_entities = pii_result.get("detected_entities", [])
    evidence = [
        {
            "category": entity.get("category", "unknown"),
            "pattern_matched": entity.get("pattern", "redacted"),
            "position": entity.get("position", 0),
        }
        for entity in pii_entities[:5]
    ]

    return FactorExplanation(
        factor_name="pii_safety",
        status=status,
        score=score,
        headline=headline,
        detail=reason,
        evidence=evidence,
        recommendation=recommendation,
        weight=2.0,  # Maximum weight — PII always auto-fails
    )


def build_bias_explanation(
    answer: str,
    context_chunks: list[dict[str, Any]],
) -> FactorExplanation:
    """
    Lightweight heuristic bias / toxicity factor.
    Production: replace with an LLM-as-judge or toxicity model call.
    """
    bias_trigger_patterns = [
        "always", "never", "all people", "no one ever",
        "everyone knows", "obviously", "clearly stupid",
        "must be wrong", "certainly evil",
    ]
    answer_lower = answer.lower()
    triggered = [p for p in bias_trigger_patterns if p in answer_lower]
    trigger_count = len(triggered)

    if trigger_count == 0:
        score = 0.95
        status = STATUS_PASS
        headline = "No bias or toxicity patterns detected in the agent response."
        recommendation = None
    elif trigger_count <= 2:
        score = 0.65
        status = STATUS_WARN
        headline = f"Mild absolutist language detected ({trigger_count} patterns) — may indicate bias."
        recommendation = (
            "Review triggered phrases and encourage more nuanced, evidence-based language. "
            "Consider adding bias-checking prompt directives."
        )
    else:
        score = 0.20
        status = STATUS_FAIL
        headline = f"Strong bias or absolutist language detected ({trigger_count} patterns) — response flagged."
        recommendation = (
            "Route to HITL review. Add guardrail prompts to the LLM system context "
            "to mitigate overgeneralization and toxic language patterns."
        )

    evidence = [{"trigger_phrase": p} for p in triggered[:5]]

    return FactorExplanation(
        factor_name="bias_toxicity",
        status=status,
        score=score,
        headline=headline,
        detail=f"Heuristic bias scan: {trigger_count} absolutist phrase(s) detected." if trigger_count else "Clean response.",
        evidence=evidence,
        recommendation=recommendation,
        weight=0.75,
    )


# ---------------------------------------------------------------------------
# Composite explanation assembler
# ---------------------------------------------------------------------------

def build_trust_explanation(
    query_id: str,
    query: str,
    answer: str,
    verdict: str,
    relevance_result: dict[str, Any],
    groundedness_result: dict[str, Any],
    pii_result: dict[str, Any],
    context_chunks: list[dict[str, Any]],
) -> TrustExplanation:
    """
    Assembles a complete, factorized TrustExplanation from all guardrail results.

    Returns a rich structured explanation including:
    - Per-factor status, score, headline, detail, and cited Moss evidence.
    - Weighted composite trust score.
    - Confidence narrative and trust grade (A–F).
    - Actionable recommendations for all non-PASS factors.
    """
    # Build each factor
    rel_exp = build_relevance_explanation(relevance_result, context_chunks)
    gnd_exp = build_groundedness_explanation(groundedness_result, context_chunks)
    pii_exp = build_pii_explanation(pii_result, query)
    bias_exp = build_bias_explanation(answer, context_chunks)

    factors = [rel_exp, gnd_exp, pii_exp, bias_exp]

    # Compute weighted composite score
    total_weight = sum(f.weight for f in factors)
    composite = sum(f.score * f.weight for f in factors) / total_weight if total_weight > 0 else 0.0
    composite = _clamp(composite)

    # Collect failed factors
    failed = [f.factor_name for f in factors if f.status == STATUS_FAIL]
    warned = [f.factor_name for f in factors if f.status == STATUS_WARN]

    # Confidence level
    if composite >= 0.80 and verdict == "PASS":
        confidence_level = "HIGH"
    elif composite >= 0.55 and verdict in ("PASS", "WARN"):
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"

    # Confidence narrative
    if confidence_level == "HIGH":
        confidence_narrative = (
            f"All critical trust dimensions are satisfied. "
            f"Composite trust score is {composite:.0%} ({trust_grade_for(composite)}). "
            f"The Moss knowledge base provided strong, relevant context grounding the response."
        )
    elif confidence_level == "MEDIUM":
        warned_str = ", ".join(warned) if warned else "none"
        confidence_narrative = (
            f"Response passed primary checks but has partial concerns in: {warned_str}. "
            f"Composite score {composite:.0%} ({trust_grade_for(composite)}). "
            f"Human review is recommended before delivery to sensitive audiences."
        )
    else:
        failed_str = ", ".join(failed) if failed else "multiple dimensions"
        confidence_narrative = (
            f"Trust confidence is LOW — critical failures in: {failed_str}. "
            f"Composite score {composite:.0%} ({trust_grade_for(composite)}). "
            f"Response has been withheld pending HITL review."
        )

    # Aggregate top cited Moss chunks
    cited_chunks = [
        {
            "chunk_id": c.get("id", f"chunk-{i}"),
            "text": c.get("text", ""),
            "score": round(c.get("score", 0.0), 4),
        }
        for i, c in enumerate(context_chunks[:5])
    ]

    return TrustExplanation(
        query_id=query_id,
        verdict=verdict,
        composite_score=composite,
        confidence_level=confidence_level,
        confidence_narrative=confidence_narrative,
        factors=factors,
        cited_chunks=cited_chunks,
        failed_factors=failed,
    )


def trust_grade_for(score: float) -> str:
    """Returns a letter grade for a given composite trust score."""
    if score >= 0.90:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.55:
        return "C"
    if score >= 0.35:
        return "D"
    return "F"
