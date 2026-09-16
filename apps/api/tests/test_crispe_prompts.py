"""
tests/test_crispe_prompts.py — Unit tests for Task 5.1
CRISPE Agent Orchestrator Prompt Templates
"""

import sys
import os
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prompts.crispe import (
    CRISPETemplate,
    ORCHESTRATOR_V1,
    VOICE_AGENT_V1,
    HITL_SUMMARIZER_V1,
    TEMPLATE_REGISTRY,
    render_orchestrator_prompt,
    render_voice_prompt,
    render_hitl_brief_prompt,
    get_template,
    _format_context,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_CHUNKS = [
    {"id": "c1", "text": "TrustMoss evaluates AI responses for reliability.", "score": 0.91},
    {"id": "c2", "text": "Moss indexes organizational knowledge for RAG pipelines.", "score": 0.84},
]

QUERY = "What does TrustMoss do?"
ANSWER = "TrustMoss evaluates AI responses for reliability using the Moss platform."


# ---------------------------------------------------------------------------
# Template registry tests
# ---------------------------------------------------------------------------

class TestTemplateRegistry:
    def test_orchestrator_in_registry(self):
        assert "ORCHESTRATOR_V1" in TEMPLATE_REGISTRY

    def test_voice_agent_in_registry(self):
        assert "VOICE_AGENT_V1" in TEMPLATE_REGISTRY

    def test_hitl_summarizer_in_registry(self):
        assert "HITL_SUMMARIZER_V1" in TEMPLATE_REGISTRY

    def test_get_template_returns_correct_instance(self):
        t = get_template("ORCHESTRATOR_V1")
        assert t is ORCHESTRATOR_V1

    def test_get_template_raises_key_error_for_unknown(self):
        with pytest.raises(KeyError, match="NONEXISTENT"):
            get_template("NONEXISTENT")


# ---------------------------------------------------------------------------
# CRISPETemplate structure tests
# ---------------------------------------------------------------------------

class TestCRISPETemplateStructure:
    def test_orchestrator_has_all_crispe_sections(self):
        t = ORCHESTRATOR_V1
        assert t.capacity.strip()
        assert t.request.strip()
        assert t.insight.strip()
        assert t.style.strip()
        assert t.persona.strip()
        assert t.execute_template.strip()

    def test_voice_template_metadata_has_lower_max_tokens(self):
        # Voice responses must be brief for TTS
        assert VOICE_AGENT_V1.metadata["max_tokens"] <= ORCHESTRATOR_V1.metadata["max_tokens"]

    def test_hitl_summarizer_is_low_temperature(self):
        # HITL briefs must be deterministic (low temp)
        assert HITL_SUMMARIZER_V1.metadata["temperature"] <= 0.15

    def test_version_fields_are_semver_format(self):
        for t in TEMPLATE_REGISTRY.values():
            parts = t.version.split(".")
            assert len(parts) == 3
            assert all(p.isdigit() for p in parts)

    def test_metadata_is_dict(self):
        for t in TEMPLATE_REGISTRY.values():
            assert isinstance(t.metadata, dict)


# ---------------------------------------------------------------------------
# Context formatter tests
# ---------------------------------------------------------------------------

class TestFormatContext:
    def test_formats_numbered_sources(self):
        result = _format_context(MOCK_CHUNKS)
        assert "[Source 1]" in result
        assert "[Source 2]" in result

    def test_includes_chunk_id(self):
        result = _format_context(MOCK_CHUNKS)
        assert "c1" in result

    def test_includes_relevance_score(self):
        result = _format_context(MOCK_CHUNKS)
        assert "0.91" in result

    def test_empty_chunks_produces_fallback_message(self):
        result = _format_context([])
        assert "No context" in result or "no context" in result.lower()

    def test_text_content_present(self):
        result = _format_context(MOCK_CHUNKS)
        assert "TrustMoss" in result


# ---------------------------------------------------------------------------
# Render helper tests
# ---------------------------------------------------------------------------

class TestRenderOrchestratorPrompt:
    def test_returns_two_strings(self):
        system, user = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_system_prompt_contains_all_crispe_sections(self):
        system, _ = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        for section in ["CAPACITY", "REQUEST", "INSIGHT", "STYLE", "PERSONA"]:
            assert section in system

    def test_user_message_contains_query(self):
        _, user = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert QUERY in user

    def test_user_message_contains_source_citations(self):
        _, user = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert "[Source 1]" in user

    def test_system_prompt_contains_version_tag(self):
        system, _ = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert ORCHESTRATOR_V1.version in system

    def test_system_prompt_contains_privacy_instruction(self):
        system, _ = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert "PII" in system or "privacy" in system.lower()

    def test_citation_instruction_is_present(self):
        system, _ = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        assert "[Source N]" in system or "Source" in system

    def test_not_empty_without_chunks(self):
        system, user = render_orchestrator_prompt(QUERY, [])
        assert len(system) > 50
        assert len(user) > 10


class TestRenderVoicePrompt:
    def test_returns_two_strings(self):
        system, user = render_voice_prompt(QUERY, MOCK_CHUNKS)
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_prompt_mentions_voice_or_tts(self):
        system, _ = render_voice_prompt(QUERY, MOCK_CHUNKS)
        assert "voice" in system.lower() or "spoken" in system.lower() or "TTS" in system

    def test_no_markdown_format_instruction_present(self):
        system, _ = render_voice_prompt(QUERY, MOCK_CHUNKS)
        assert "markdown" in system.lower() or "bullet" in system.lower()

    def test_user_message_contains_query(self):
        _, user = render_voice_prompt(QUERY, MOCK_CHUNKS)
        assert QUERY in user


class TestRenderHITLBriefPrompt:
    def test_returns_two_strings(self):
        system, user = render_hitl_brief_prompt(
            query=QUERY,
            answer=ANSWER,
            failed_factors=["groundedness", "bias_toxicity"],
            context_chunks=MOCK_CHUNKS,
        )
        assert isinstance(system, str) and isinstance(user, str)

    def test_user_message_contains_original_query(self):
        _, user = render_hitl_brief_prompt(QUERY, ANSWER, [], MOCK_CHUNKS)
        assert QUERY in user

    def test_user_message_contains_answer(self):
        _, user = render_hitl_brief_prompt(QUERY, ANSWER, [], MOCK_CHUNKS)
        assert ANSWER in user

    def test_user_message_contains_failed_factors(self):
        _, user = render_hitl_brief_prompt(QUERY, ANSWER, ["pii_safety"], MOCK_CHUNKS)
        assert "pii_safety" in user

    def test_no_failed_factors_shows_manual_escalation(self):
        _, user = render_hitl_brief_prompt(QUERY, ANSWER, [], MOCK_CHUNKS)
        assert "None" in user or "manual" in user.lower()

    def test_system_prompt_has_hitl_instructions(self):
        system, _ = render_hitl_brief_prompt(QUERY, ANSWER, [], MOCK_CHUNKS)
        assert "reviewer" in system.lower() or "HITL" in system or "audit" in system.lower()


# ---------------------------------------------------------------------------
# Integration: raw render produces valid non-empty content
# ---------------------------------------------------------------------------

class TestTemplateRenderIntegration:
    def test_all_templates_render_without_exception(self):
        for name, tmpl in TEMPLATE_REGISTRY.items():
            try:
                if name == "HITL_SUMMARIZER_V1":
                    sys_p, usr_p = tmpl.render(
                        query=QUERY,
                        context_chunks=MOCK_CHUNKS,
                        extra={"answer": ANSWER, "failed_factors": "groundedness"},
                    )
                else:
                    sys_p, usr_p = tmpl.render(query=QUERY, context_chunks=MOCK_CHUNKS)
                assert len(sys_p) > 50, f"{name} system prompt too short"
                assert len(usr_p) > 10, f"{name} user message too short"
            except Exception as e:
                pytest.fail(f"Template '{name}' render raised: {e}")

    def test_orchestrator_prompt_not_same_as_voice_prompt(self):
        orch_sys, orch_usr = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        voice_sys, voice_usr = render_voice_prompt(QUERY, MOCK_CHUNKS)
        # Templates must be distinct — different roles
        assert orch_sys != voice_sys

    def test_rendered_content_is_string_encodable(self):
        system, user = render_orchestrator_prompt(QUERY, MOCK_CHUNKS)
        try:
            _ = system.encode("utf-8")
            _ = user.encode("utf-8")
        except UnicodeEncodeError:
            pytest.fail("Rendered prompt contains non-UTF-8 characters")
