"""
guardrails/groundedness.py — Guardrail 2: Groundedness Check (stub for baseline).

Runs AFTER the LLM generates an answer.
Full implementation (Day 3): embed answer + context, compute cosine similarity.
Baseline stub: returns a PASS with a note that full check is pending.

Returns:
    {
        "passed": bool,
        "score": float,
        "reason": str
    }
"""


def check(answer: str, context_chunks: list) -> dict:
    """
    Baseline stub — always passes so the pipeline runs end-to-end.
    Day 3: replace body with embedding + cosine similarity logic.

    Args:
        answer: The LLM-generated response text.
        context_chunks: List of {"id", "text", "score"} dicts from Moss.

    Returns:
        GuardResult dict.
    """
    return {
        "passed": True,
        "score": -1.0,  # -1 signals "not yet computed"
        "reason": "Groundedness check not yet implemented (baseline stub — Day 3).",
    }
