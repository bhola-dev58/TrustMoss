"""
trust_score.py — Aggregates the three guardrail results into a final trust verdict.

Logic (as defined in the PRD):
  • All 3 pass                       → PASS  (green)
  • Exactly 1 fails / warns          → WARN  (yellow)
  • 2+ fail  OR  PII found           → FAIL  (red)

Returns:
    {
        "verdict":  "PASS" | "WARN" | "FAIL",
        "color":    "green" | "yellow" | "red",
        "score":    float,   # 0.0 – 1.0
        "reason":   str
    }
"""

from typing import Dict


def aggregate(
    relevance_result: Dict,
    groundedness_result: Dict,
    pii_result: Dict,
) -> Dict:
    """
    Combine the three guardrail results into a single trust verdict.

    Args:
        relevance_result:      Output of guardrails.relevance.check()
        groundedness_result:   Output of guardrails.groundedness.check()
        pii_result:            Output of guardrails.pii_scan.check()

    Returns:
        Trust verdict dict.
    """
    failed_checks = []
    reasons = []

    # Collect failures
    if not relevance_result["passed"]:
        failed_checks.append("relevance")
        reasons.append(f"Context relevance: {relevance_result['reason']}")

    # Groundedness: skip if stub (score == -1)
    if groundedness_result["score"] != -1.0 and not groundedness_result["passed"]:
        failed_checks.append("groundedness")
        reasons.append(f"Groundedness: {groundedness_result['reason']}")

    # PII always counts if it fails (auto-FAIL)
    pii_detected = not pii_result["passed"]
    if pii_detected:
        failed_checks.append("pii")
        reasons.append(f"PII detected: {pii_result['reason']}")

    n_failed = len(failed_checks)

    # Determine verdict
    if n_failed == 0:
        verdict = "PASS"
        color = "green"
        score = 1.0
        summary = "All guardrail checks passed. Response is safe to deliver."
    elif n_failed == 1 and not pii_detected:
        verdict = "WARN"
        color = "yellow"
        score = 0.5
        summary = f"One check flagged: {', '.join(failed_checks)}. Review recommended."
    else:
        verdict = "FAIL"
        color = "red"
        score = 0.0
        summary = f"Multiple checks failed or PII detected: {', '.join(failed_checks)}. Response withheld."

    return {
        "verdict": verdict,
        "color": color,
        "score": score,
        "reason": summary,
        "details": reasons,
        "failed_checks": failed_checks,
    }
