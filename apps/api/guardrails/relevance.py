"""
guardrails/relevance.py — Guardrail 1: Context Relevance Check.

Runs BEFORE the LLM call.
Reads Moss's top relevance score from the retrieval result.
If it's below the configured threshold, the context is likely not useful.

Returns:
    {
        "passed": bool,
        "score": float,
        "reason": str
    }
"""

import os

from dotenv import load_dotenv

load_dotenv()

RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.6"))


def check(top_score: float) -> dict:
    """
    Args:
        top_score: The highest relevance score returned by Moss retrieval.

    Returns:
        GuardResult dict with passed, score, and a human-readable reason.
    """
    passed = top_score >= RELEVANCE_THRESHOLD

    if passed:
        reason = f"Top context relevance score {top_score:.2f} meets threshold ({RELEVANCE_THRESHOLD})."
    else:
        reason = (
            f"Top context relevance score {top_score:.2f} is below threshold ({RELEVANCE_THRESHOLD}). "
            "The knowledge base may not contain relevant information for this query."
        )

    return {
        "passed": passed,
        "score": round(top_score, 4),
        "reason": reason,
    }
