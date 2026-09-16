"""
tests/test_explainability.py — Unit + integration tests for Task 4.4
Trust Score Explainability Framework
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import explainability
from explainability import (
    build_relevance_explanation,
    build_groundedness_explanation,
    build_pii_explanation,
    build_bias_explanation,
    build_trust_explanation,
    trust_grade_for,
    STATUS_PASS,
    STATUS_WARN,
    STATUS_FAIL,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_CHUNKS = [
    {"id": "chunk-1", "text": "Moss is a knowledge management platform.", "score": 0.91},
    {"id": "chunk-2", "text": "TrustMoss evaluates AI responses for reliability.", "score": 0.82},
    {"id": "chunk-3", "text": "HITL queues route low-trust answers to human reviewers.", "score": 0.74},
]

RELEVANCE_PASS = {"passed": True, "score": 0.88, "reason": "Score meets threshold."}
RELEVANCE_WARN = {"passed": False, "score": 0.63, "reason": "Score below threshold."}
RELEVANCE_FAIL = {"passed": False, "score": 0.30, "reason": "Score critically low."}

GROUNDEDNESS_STUB = {"passed": True, "score": -1.0, "reason": "Stub — Day 3."}
GROUNDEDNESS_PASS = {"passed": True, "score": 0.90, "reason": "High overlap with context."}
GROUNDEDNESS_FAIL = {"passed": False, "score": 0.40, "reason": "Hallucination detected."}

PII_PASS = {"passed": True, "score": 1.0, "reason": "No PII.", "redacted_answer": "safe answer"}
PII_FAIL = {"passed": False, "score": 0.10, "reason": "SSN detected.", "detected_entities": [{"category": "SSN", "pattern": "###-##-####", "position": 5}]}

CLEAN_ANSWER = "The system processes requests efficiently and securely."
BIASED_ANSWER = "Everyone knows this is obviously wrong. All people clearly agree this is never correct."


# ---------------------------------------------------------------------------
# Unit tests — factor builders
# ---------------------------------------------------------------------------

class TestRelevanceExplanation:
    def test_pass_produces_pass_status(self):
        exp = build_relevance_explanation(RELEVANCE_PASS, MOCK_CHUNKS)
        assert exp.status == STATUS_PASS
        assert exp.score >= 0.85

    def test_warn_produces_warn_status(self):
        exp = build_relevance_explanation(RELEVANCE_WARN, MOCK_CHUNKS)
        assert exp.status == STATUS_WARN
        assert exp.recommendation is not None

    def test_fail_produces_fail_status(self):
        exp = build_relevance_explanation(RELEVANCE_FAIL, MOCK_CHUNKS)
        assert exp.status == STATUS_FAIL
        assert exp.recommendation is not None

    def test_evidence_contains_top_chunks(self):
        exp = build_relevance_explanation(RELEVANCE_PASS, MOCK_CHUNKS)
        assert len(exp.evidence) <= 3
        assert exp.evidence[0]["chunk_id"] == "chunk-1"

    def test_weight_is_positive(self):
        exp = build_relevance_explanation(RELEVANCE_PASS, MOCK_CHUNKS)
        assert exp.weight > 0

    def test_to_dict_schema(self):
        d = build_relevance_explanation(RELEVANCE_PASS, MOCK_CHUNKS).to_dict()
        required = {"factor_name", "status", "score", "headline", "detail", "evidence", "recommendation", "weight"}
        assert required.issubset(d.keys())


class TestGroundednessExplanation:
    def test_stub_score_treated_as_pass(self):
        exp = build_groundedness_explanation(GROUNDEDNESS_STUB, MOCK_CHUNKS)
        assert exp.status == STATUS_PASS
        # Recommendation should mention production upgrade
        assert "production" in exp.recommendation.lower() or "stub" in exp.recommendation.lower()

    def test_strong_groundedness_pass(self):
        exp = build_groundedness_explanation(GROUNDEDNESS_PASS, MOCK_CHUNKS)
        assert exp.status == STATUS_PASS
        assert exp.recommendation is None

    def test_groundedness_failure(self):
        exp = build_groundedness_explanation(GROUNDEDNESS_FAIL, MOCK_CHUNKS)
        assert exp.status == STATUS_FAIL
        assert "HITL" in exp.recommendation

    def test_groundedness_weight_is_higher(self):
        # Groundedness is the most critical signal, should have weight > 1
        exp = build_groundedness_explanation(GROUNDEDNESS_PASS, MOCK_CHUNKS)
        assert exp.weight > 1.0


class TestPIIExplanation:
    def test_clean_answer_passes(self):
        exp = build_pii_explanation(PII_PASS, "what is moss?")
        assert exp.status == STATUS_PASS
        assert exp.recommendation is None

    def test_pii_detected_fails(self):
        exp = build_pii_explanation(PII_FAIL, "what is the user ssn?")
        assert exp.status == STATUS_FAIL
        assert "HITL" in exp.recommendation

    def test_pii_evidence_extracts_entities(self):
        exp = build_pii_explanation(PII_FAIL, "test query")
        assert len(exp.evidence) >= 1
        assert exp.evidence[0]["category"] == "SSN"

    def test_pii_weight_is_maximum(self):
        # PII should carry the highest weight of all factors
        exp_pii = build_pii_explanation(PII_PASS, "q")
        exp_gnd = build_groundedness_explanation(GROUNDEDNESS_PASS, MOCK_CHUNKS)
        assert exp_pii.weight >= exp_gnd.weight


class TestBiasExplanation:
    def test_clean_answer_passes(self):
        exp = build_bias_explanation(CLEAN_ANSWER, MOCK_CHUNKS)
        assert exp.status == STATUS_PASS

    def test_biased_answer_flagged(self):
        exp = build_bias_explanation(BIASED_ANSWER, MOCK_CHUNKS)
        assert exp.status in (STATUS_WARN, STATUS_FAIL)
        assert len(exp.evidence) > 0

    def test_evidence_contains_trigger_phrases(self):
        exp = build_bias_explanation(BIASED_ANSWER, MOCK_CHUNKS)
        phrases = [e["trigger_phrase"] for e in exp.evidence]
        assert any("obviously" in p or "everyone knows" in p for p in phrases)


# ---------------------------------------------------------------------------
# Integration tests — composite explanation
# ---------------------------------------------------------------------------

class TestBuildTrustExplanation:
    def _make_explanation(self, relevance=RELEVANCE_PASS, groundedness=GROUNDEDNESS_STUB,
                          pii=PII_PASS, answer=CLEAN_ANSWER, verdict="PASS"):
        return build_trust_explanation(
            query_id="test-qid-001",
            query="what is trustvault?",
            answer=answer,
            verdict=verdict,
            relevance_result=relevance,
            groundedness_result=groundedness,
            pii_result=pii,
            context_chunks=MOCK_CHUNKS,
        )

    def test_schema_completeness(self):
        exp = self._make_explanation()
        d = exp.to_dict()
        required_keys = {
            "query_id", "verdict", "composite_score", "trust_grade",
            "confidence_level", "confidence_narrative", "factors",
            "cited_chunks", "failed_factors",
        }
        assert required_keys.issubset(d.keys())

    def test_four_factors_always_present(self):
        exp = self._make_explanation()
        factor_names = [f.factor_name for f in exp.factors]
        assert "context_relevance" in factor_names
        assert "groundedness" in factor_names
        assert "pii_safety" in factor_names
        assert "bias_toxicity" in factor_names

    def test_composite_score_bounded(self):
        exp = self._make_explanation()
        assert 0.0 <= exp.composite_score <= 1.0

    def test_high_confidence_all_pass(self):
        exp = self._make_explanation(
            relevance=RELEVANCE_PASS,
            groundedness=GROUNDEDNESS_PASS,
            verdict="PASS",
        )
        assert exp.confidence_level in ("HIGH", "MEDIUM")

    def test_low_confidence_when_pii_fails(self):
        exp = self._make_explanation(pii=PII_FAIL, verdict="FAIL")
        assert exp.confidence_level == "LOW"
        assert "pii_safety" in exp.failed_factors

    def test_trust_grade_f_when_composite_is_low(self):
        exp = self._make_explanation(
            relevance=RELEVANCE_FAIL,
            groundedness=GROUNDEDNESS_FAIL,
            pii=PII_FAIL,
            verdict="FAIL",
        )
        # All factors fail → very low composite → grade F or D
        assert exp.trust_grade in ("F", "D")

    def test_trust_grade_for_function(self):
        assert trust_grade_for(0.95) == "A"
        assert trust_grade_for(0.80) == "B"
        assert trust_grade_for(0.60) == "C"
        assert trust_grade_for(0.40) == "D"
        assert trust_grade_for(0.10) == "F"

    def test_cited_chunks_capped_at_five(self):
        extra_chunks = MOCK_CHUNKS * 4  # 12 chunks
        exp = build_trust_explanation(
            query_id="q2",
            query="test",
            answer=CLEAN_ANSWER,
            verdict="PASS",
            relevance_result=RELEVANCE_PASS,
            groundedness_result=GROUNDEDNESS_PASS,
            pii_result=PII_PASS,
            context_chunks=extra_chunks,
        )
        assert len(exp.cited_chunks) <= 5

    def test_recommendations_present_when_fail(self):
        exp = self._make_explanation(relevance=RELEVANCE_FAIL, verdict="WARN")
        failing_factor = next(f for f in exp.factors if f.factor_name == "context_relevance")
        assert failing_factor.recommendation is not None

    def test_to_dict_is_json_serializable(self):
        import json
        exp = self._make_explanation()
        try:
            serialized = json.dumps(exp.to_dict())
            assert len(serialized) > 100
        except (TypeError, ValueError) as e:
            pytest.fail(f"TrustExplanation.to_dict() produced non-JSON-serializable output: {e}")
