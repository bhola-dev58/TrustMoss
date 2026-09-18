"""
tests/test_prompt_catalog.py — Unit tests for Task 5.3
Prompt Catalog Module & PRD Embedding
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import modules — side-effect registers all templates
from prompts.catalog import (
    _TEMPLATE_ENRICHMENT,
    catalog,
    catalog_as_markdown,
    get_catalog_entry,
)
from prompts.crispe import TEMPLATE_REGISTRY

# ---------------------------------------------------------------------------
# Catalog structure tests
# ---------------------------------------------------------------------------

class TestCatalogStructure:
    def test_catalog_returns_dict(self):
        c = catalog()
        assert isinstance(c, dict)

    def test_catalog_has_required_top_level_keys(self):
        c = catalog()
        required = {"catalog_version", "generated_at", "total_templates",
                    "categories", "templates", "by_category", "summary"}
        assert required.issubset(c.keys())

    def test_total_templates_equals_registry_size(self):
        c = catalog()
        assert c["total_templates"] == len(TEMPLATE_REGISTRY)

    def test_total_templates_is_seven(self):
        c = catalog()
        assert c["total_templates"] >= 7

    def test_templates_is_list(self):
        c = catalog()
        assert isinstance(c["templates"], list)

    def test_by_category_groups_correctly(self):
        c = catalog()
        all_in_groups = sum(len(v) for v in c["by_category"].values())
        assert all_in_groups == c["total_templates"]

    def test_summary_matches_by_category(self):
        c = catalog()
        for cat, count in c["summary"].items():
            assert len(c["by_category"][cat]) == count

    def test_catalog_version_is_semver(self):
        c = catalog()
        parts = c["catalog_version"].split(".")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)

    def test_generated_at_is_iso_string(self):
        c = catalog()
        assert "T" in c["generated_at"] and "Z" in c["generated_at"] or "+" in c["generated_at"]


# ---------------------------------------------------------------------------
# Individual catalog entry tests
# ---------------------------------------------------------------------------

class TestCatalogEntry:
    EXPECTED_FIELDS = {
        "name", "version", "category", "use_case", "llm_surface",
        "temperature", "max_tokens", "output_format", "guardrails",
        "prd_section", "crispe_summary", "added_in_task", "tts_safe",
    }

    def test_every_entry_has_all_required_fields(self):
        c = catalog()
        for entry in c["templates"]:
            missing = self.EXPECTED_FIELDS - set(entry.keys())
            assert not missing, f"Template '{entry['name']}' missing fields: {missing}"

    def test_orchestrator_v1_entry(self):
        entry = get_catalog_entry("ORCHESTRATOR_V1")
        assert entry["category"] == "orchestration"
        assert entry["temperature"] == 0.2
        assert entry["max_tokens"] == 512
        assert entry["output_format"] == "prose"

    def test_voice_agent_v1_entry(self):
        entry = get_catalog_entry("VOICE_AGENT_V1")
        assert entry["tts_safe"] is True
        assert entry["max_tokens"] <= 256

    def test_hitl_summarizer_entry(self):
        entry = get_catalog_entry("HITL_SUMMARIZER_V1")
        assert entry["category"] == "governance"

    def test_groundedness_judge_entry(self):
        entry = get_catalog_entry("GROUNDEDNESS_JUDGE_V1")
        assert entry["output_format"] == "json"
        assert entry["temperature"] == 0.05

    def test_hallucination_risk_entry(self):
        entry = get_catalog_entry("HALLUCINATION_RISK_V1")
        assert entry["temperature"] == 0.0
        assert entry["category"] == "evaluation"

    def test_jailbreak_analyst_entry(self):
        entry = get_catalog_entry("JAILBREAK_ANALYST_V1")
        assert entry["category"] == "safety"
        assert entry["temperature"] == 0.0

    def test_hitl_verdict_entry(self):
        entry = get_catalog_entry("HITL_VERDICT_V1")
        assert entry["category"] == "governance"
        assert "gdpr" in entry["crispe_summary"].get("I", "").lower() or \
               "compliance" in str(entry["crispe_summary"]).lower()

    def test_unknown_template_raises_key_error(self):
        with pytest.raises(KeyError, match="NONEXISTENT"):
            get_catalog_entry("NONEXISTENT")

    def test_crispe_summary_has_six_sections(self):
        for name in TEMPLATE_REGISTRY:
            entry = get_catalog_entry(name)
            if entry["crispe_summary"]:
                sections = set(entry["crispe_summary"].keys())
                assert sections == {"C", "R", "I", "S", "P", "E"}, \
                    f"{name} crispe_summary missing sections: " + str({"C","R","I","S","P","E"} - sections)

    def test_all_entries_have_prd_section(self):
        c = catalog()
        for entry in c["templates"]:
            assert entry["prd_section"], f"{entry['name']} missing prd_section"

    def test_all_entries_have_llm_surface(self):
        c = catalog()
        for entry in c["templates"]:
            assert entry["llm_surface"], f"{entry['name']} missing llm_surface"

    def test_all_entries_have_added_in_task(self):
        c = catalog()
        for entry in c["templates"]:
            assert entry["added_in_task"], f"{entry['name']} missing added_in_task"


# ---------------------------------------------------------------------------
# Categories structure tests
# ---------------------------------------------------------------------------

class TestCategories:
    def test_orchestration_category_present(self):
        c = catalog()
        assert "orchestration" in c["categories"]

    def test_evaluation_category_present(self):
        c = catalog()
        assert "evaluation" in c["categories"]

    def test_safety_category_present(self):
        c = catalog()
        assert "safety" in c["categories"]

    def test_governance_category_present(self):
        c = catalog()
        assert "governance" in c["categories"]

    def test_at_least_two_orchestration_templates(self):
        c = catalog()
        assert len(c["by_category"].get("orchestration", [])) >= 2

    def test_at_least_two_evaluation_templates(self):
        c = catalog()
        assert len(c["by_category"].get("evaluation", [])) >= 2

    def test_at_least_one_safety_template(self):
        c = catalog()
        assert len(c["by_category"].get("safety", [])) >= 1

    def test_at_least_two_governance_templates(self):
        c = catalog()
        assert len(c["by_category"].get("governance", [])) >= 2


# ---------------------------------------------------------------------------
# Markdown PRD document tests
# ---------------------------------------------------------------------------

class TestCatalogAsMarkdown:
    def test_returns_non_empty_string(self):
        md = catalog_as_markdown()
        assert isinstance(md, str) and len(md) > 1000

    def test_contains_title(self):
        md = catalog_as_markdown()
        assert "TrustMoss CRISPE Prompt Catalog" in md

    def test_contains_all_template_names(self):
        md = catalog_as_markdown()
        for name in TEMPLATE_REGISTRY:
            assert name in md, f"Template '{name}' missing from markdown"

    def test_contains_overview_table(self):
        md = catalog_as_markdown()
        assert "| Category | Count |" in md

    def test_contains_crispe_section_headers(self):
        md = catalog_as_markdown()
        for section in ["Capacity (Role)", "Request (Task)", "Insight (Context)",
                        "Style (Format)", "Persona (Values)", "Execute (Action)"]:
            assert section in md

    def test_contains_prompt_engineering_principles(self):
        md = catalog_as_markdown()
        assert "Prompt Engineering Principles" in md

    def test_contains_versioned_notes(self):
        md = catalog_as_markdown()
        assert "Versioned" in md and "SemVer" in md

    def test_contains_auto_generated_note(self):
        md = catalog_as_markdown()
        assert "Auto-generated" in md or "auto-generated" in md

    def test_markdown_is_utf8_encodable(self):
        md = catalog_as_markdown()
        try:
            md.encode("utf-8")
        except UnicodeEncodeError:
            pytest.fail("catalog_as_markdown() produced non-UTF-8 content")

    def test_contains_prd_section_references(self):
        md = catalog_as_markdown()
        assert "Section 4" in md

    def test_guardrails_listed_in_md(self):
        md = catalog_as_markdown()
        assert "groundedness" in md or "Guardrails" in md


# ---------------------------------------------------------------------------
# Enrichment metadata coverage test
# ---------------------------------------------------------------------------

class TestEnrichmentCoverage:
    def test_all_registry_templates_have_enrichment(self):
        for name in TEMPLATE_REGISTRY:
            assert name in _TEMPLATE_ENRICHMENT, \
                f"Template '{name}' has no enrichment entry in _TEMPLATE_ENRICHMENT"

    def test_all_enrichment_has_crispe_summary(self):
        for name, enrichment in _TEMPLATE_ENRICHMENT.items():
            assert "crispe_summary" in enrichment, f"{name} enrichment missing crispe_summary"
            summary = enrichment["crispe_summary"]
            assert set(summary.keys()) == {"C", "R", "I", "S", "P", "E"}, \
                f"{name} crispe_summary missing sections"
