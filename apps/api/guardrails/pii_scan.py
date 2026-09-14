"""
guardrails/pii_scan.py — Guardrail 3: PII / Sensitive Data Scan (stub for baseline).

Runs on the final LLM answer BEFORE it is returned to the user.
Full implementation (Day 4): regex patterns for email, phone, SSN, credit card, API keys.
Baseline stub: returns PASS so the pipeline runs end-to-end.

Returns:
    {
        "passed": bool,
        "score": float,
        "reason": str,
        "redacted_answer": str   <- same as input in stub; redacted version in full impl
    }
"""


def check(answer: str) -> dict:
    """
    Baseline stub — always passes.
    Day 4: replace body with regex PII detection + optional redaction.

    Args:
        answer: The LLM-generated response text.

    Returns:
        GuardResult dict with an additional `redacted_answer` field.
    """
    return {
        "passed": True,
        "score": 1.0,
        "reason": "PII scan not yet implemented (baseline stub — Day 4).",
        "redacted_answer": answer,
    }
