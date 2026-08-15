"""Rigorous consistency and XML schema tests across AGENTS.md and all 12 adapters."""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_PATH = os.path.join(REPO_ROOT, "AGENTS.md")
ADAPTERS_DIR = os.path.join(REPO_ROOT, "adapters")

EXPECTED_ADAPTERS = [
    "aider.md",
    "claude.md",
    "cline.md",
    "cody.md",
    "continue.md",
    "copilot-instructions.md",
    "cursor.mdc",
    "gemini.md",
    "jetbrains.md",
    "openhands.md",
    "windsurf.md",
    "zed.md",
]


def extract_xml_block(content: str) -> str:
    """Extract <autoevolve_mindset>...</autoevolve_mindset> block."""
    match = re.search(r"(<autoevolve_mindset>[\s\S]*?</autoevolve_mindset>)", content)
    assert match is not None, "Failed to find <autoevolve_mindset> block in content"
    return match.group(1).strip()


class TestAdapterConsistency:
    def test_agents_md_exists_and_is_valid_xml(self):
        assert os.path.isfile(AGENTS_PATH), "AGENTS.md must exist at repository root"
        with open(AGENTS_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        xml_str = extract_xml_block(content)
        # Parse XML tree
        root = ET.fromstring(xml_str)
        assert root.tag == "autoevolve_mindset"

        # Check required tags
        child_tags = [child.tag for child in root]
        assert "role" in child_tags
        assert "loop" in child_tags
        assert "ladder" in child_tags
        assert "guardrails" in child_tags
        assert "conventions" in child_tags
        assert "autonomy" in child_tags

    def test_all_12_adapters_exist(self):
        assert os.path.isdir(ADAPTERS_DIR), "adapters/ directory must exist"
        present_adapters = sorted(os.listdir(ADAPTERS_DIR))
        for expected in EXPECTED_ADAPTERS:
            assert expected in present_adapters, f"Missing adapter: {expected}"

    @pytest.mark.parametrize("adapter_name", EXPECTED_ADAPTERS)
    def test_adapter_contains_core_marker(self, adapter_name):
        path = os.path.join(ADAPTERS_DIR, adapter_name)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<!-- AutoEvolve-Core -->" in content or adapter_name.endswith(".mdc"), (
            f"Adapter {adapter_name} missing <!-- AutoEvolve-Core --> marker"
        )

    @pytest.mark.parametrize("adapter_name", EXPECTED_ADAPTERS)
    def test_adapter_xml_matches_agents_md(self, adapter_name):
        """Verify 0% drift in the core XML prompt across all 12 adapters."""
        with open(AGENTS_PATH, "r", encoding="utf-8") as f:
            canonical_xml = extract_xml_block(f.read())

        path = os.path.join(ADAPTERS_DIR, adapter_name)
        with open(path, "r", encoding="utf-8") as f:
            adapter_content = f.read()

        adapter_xml = extract_xml_block(adapter_content)
        assert adapter_xml == canonical_xml, (
            f"Adapter {adapter_name} has drifted from canonical AGENTS.md XML block"
        )

    @pytest.mark.parametrize("adapter_name", EXPECTED_ADAPTERS)
    def test_adapter_xml_is_well_formed(self, adapter_name):
        path = os.path.join(ADAPTERS_DIR, adapter_name)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        xml_str = extract_xml_block(content)
        root = ET.fromstring(xml_str)
        assert root.tag == "autoevolve_mindset"
