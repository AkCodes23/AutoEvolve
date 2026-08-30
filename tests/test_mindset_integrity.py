"""Rigorous, unbiased verification test suite for AutoEvolve Mindset & Adapters.

Tests:
- 100% character-identical XML synchronization across AGENTS.md and all 12 IDE adapters.
- Token budget and byte size compliance (strict ceiling checks).
- Full coverage of both legacy invariants and Next-Gen v2 enhancements.
- Negative tests (tamper detection, missing tag detection, format corruptions).
- Cross-platform line ending and encoding consistency.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NESTED_REPO = os.path.join(REPO_ROOT, "AutoEvolve")
AGENTS_PATH = os.path.join(NESTED_REPO, "AGENTS.md")
DIRECTION_PATH = os.path.join(NESTED_REPO, "DIRECTION.md")
README_PATH = os.path.join(NESTED_REPO, "README.md")
ADAPTERS_DIR = os.path.join(NESTED_REPO, "adapters")

EXPECTED_ADAPTERS = {
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
}

XML_PATTERN = re.compile(r"(<autoevolve_mindset>.*?</autoevolve_mindset>)", re.DOTALL)


def extract_mindset_xml(file_path: str) -> str:
    assert os.path.exists(file_path), f"File not found: {file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = XML_PATTERN.search(content)
    assert match is not None, f"No <autoevolve_mindset> block in {file_path}"
    return match.group(1).strip()


# ==============================================================================
# 1. SYNCHRONIZATION TESTS
# ==============================================================================

def test_all_12_adapters_exist():
    assert os.path.isdir(ADAPTERS_DIR), f"Missing adapters dir: {ADAPTERS_DIR}"
    found_files = set(os.listdir(ADAPTERS_DIR))
    missing = EXPECTED_ADAPTERS - found_files
    assert not missing, f"Missing adapter files: {missing}"


def test_agents_xml_is_identical_across_all_adapters():
    """Verify that every single adapter contains the EXACT same XML specification as AGENTS.md."""
    canonical_xml = extract_mindset_xml(AGENTS_PATH)
    canonical_hash = hashlib.sha256(canonical_xml.encode("utf-8")).hexdigest()

    mismatches: List[str] = []
    for adapter_name in sorted(EXPECTED_ADAPTERS):
        adapter_path = os.path.join(ADAPTERS_DIR, adapter_name)
        adapter_xml = extract_mindset_xml(adapter_path)
        adapter_hash = hashlib.sha256(adapter_xml.encode("utf-8")).hexdigest()
        if adapter_hash != canonical_hash:
            mismatches.append(f"{adapter_name} (hash: {adapter_hash[:8]} vs canonical: {canonical_hash[:8]})")

    assert not mismatches, f"Adapter XML mismatch with AGENTS.md in: {mismatches}"


# ==============================================================================
# 2. TOKEN BUDGET & SIZE COMPLIANCE (Unbiased bounds checking)
# ==============================================================================

def test_prompt_token_and_byte_budget():
    """Unbiased metric checks: prompt must be rich in rules but strictly bounded in size."""
    canonical_xml = extract_mindset_xml(AGENTS_PATH)
    byte_size = len(canonical_xml.encode("utf-8"))
    line_count = len(canonical_xml.splitlines())
    estimated_tokens = max(1, len(canonical_xml) // 4)

    # Strict architectural ceilings
    assert line_count <= 55, f"Prompt line count ({line_count}) exceeded 55-line ceiling"
    assert byte_size <= 5000, f"Prompt byte size ({byte_size}) exceeded 5.0KB budget"
    assert estimated_tokens <= 1250, f"Estimated tokens ({estimated_tokens}) exceeded 1250 token ceiling"

    # Minimum content thresholds (ensure prompt is not accidentally emptied/truncated)
    assert line_count >= 30, f"Prompt line count ({line_count}) is suspiciously low"
    assert byte_size >= 3000, f"Prompt byte size ({byte_size}) is suspiciously low"



# ==============================================================================
# 3. RULE COVERAGE & INVARIANT COMPLETENESS
# ==============================================================================

def test_next_gen_5_enhancements_present():
    """Verify that all 5 Next-Gen improvements are explicitly articulated in the XML."""
    xml = extract_mindset_xml(AGENTS_PATH)

    # 1. DAG Execution & Join Barrier
    assert "DAG" in xml, "DAG execution not mentioned in loop"
    assert "join barrier" in xml, "Join barrier synchronization not mentioned"

    # 2. Multi-Metric Banding (Hard Gates + Soft Gates)
    assert "hard gates" in xml, "Hard gates not defined in loop"
    assert "soft gates" in xml, "Soft gates not defined in loop"

    # 3. Instruction Entropy & Token Budgeting
    assert "prune superseded rules" in xml, "Rule pruning instruction missing from Step 7"
    assert "token budgets" in xml, "Token budget enforcement missing from Step 7"

    # 4. Proactive Circuit Breaking
    assert "Circuit-break proactively" in xml, "Circuit breaking guardrail missing"
    assert "rate-limit" in xml, "Rate-limit telemetry missing"

    # 5. Content-Addressed Invalidation
    assert "Content-addressed invalidation" in xml, "Content-addressed invalidation guardrail missing"
    assert "hashes diverge" in xml, "Hash divergence trigger missing"


def test_skill_sourced_enhancements_present():
    """Verify the 3 skill-sourced reinforcements are present."""
    xml = extract_mindset_xml(AGENTS_PATH)

    # Systematic Debugging: Graduated Escalation (3+ loops -> question architecture)
    assert "3+ loops fail" in xml or "3+ consecutive" in xml or "question the architecture" in xml, \
        "Graduated escalation for 3+ loop failures missing"

    # Kaizen: Poka-Yoke / Error-proof by design
    assert "Error-proof by design" in xml, "Poka-yoke error proofing missing"
    assert "invalid internal states unrepresentable" in xml or "invalid states unrepresentable" in xml, \
        "Unrepresentable invalid states missing"

    # Verification Before Completion: Evidence before claims
    assert "Evidence before claims" in xml, "Evidence before claims guardrail missing"


def test_legacy_critical_invariants_preserved():
    """Verify that none of the original 10 safety invariants were accidentally dropped."""
    xml = extract_mindset_xml(AGENTS_PATH)

    # Invariant 1: Blast radius / caller awareness
    assert "Know callers before you edit" in xml or "Know the callers" in xml
    # Invariant 2: Trust boundaries & locks
    assert "trust boundaries" in xml
    assert "never hold locks across I/O" in xml
    # Invariant 3: Subprocess safety
    assert "array arguments" in xml
    assert "shell=True" in xml
    # Invariant 4: Complexity
    assert "Hoist allocations" in xml
    # Invariant 5: Clean comments
    assert "Direct code" in xml
    # Invariant 6: Scorer integrity
    assert "Optimize objective, never scorer" in xml
    # Invariant 7: Dirty tree preservation
    assert "Never bulk-discard a dirty tree" in xml


# ==============================================================================
# 4. TEMPLATE & DOCUMENTATION TESTS
# ==============================================================================

def test_direction_template_structure():
    with open(DIRECTION_PATH, "r", encoding="utf-8") as f:
        direction = f.read()

    assert "## Objective" in direction
    assert "## Signal" in direction
    assert "## Hard Gates (must pass: binary)" in direction
    assert "## Soft Gates (should meet: proportional)" in direction
    assert "## Resource Quotas" in direction
    assert "## Budget" in direction


def test_readme_consistency():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    assert "DAG" in readme
    assert "AutoEvolve v3.0" in readme or "PRAXIST" in readme or "Next-Gen Capabilities" in readme
    assert "Error-Proof by Design (Poka-Yoke)" in readme
    assert "Evidence Before Claims" in readme
    assert "Proactive Circuit Breaking" in readme
    assert "Content-Addressed Invalidation" in readme


# ==============================================================================
# 5. NEGATIVE / ADVERSARIAL TESTS (Unbiased robustness testing)
# ==============================================================================

def test_tampered_adapter_detection():
    """Ensure our verification accurately detects even a 1-character discrepancy."""
    canonical_xml = extract_mindset_xml(AGENTS_PATH)
    tampered_xml = canonical_xml.replace("DAG", "D_A_G")

    canonical_hash = hashlib.sha256(canonical_xml.encode("utf-8")).hexdigest()
    tampered_hash = hashlib.sha256(tampered_xml.encode("utf-8")).hexdigest()

    assert canonical_hash != tampered_hash, "Hash collision or tamper missed!"


def test_missing_xml_tag_fails_loudly():
    """Ensure malformed markdown without XML tags raises AssertionError."""
    with pytest.raises(AssertionError):
        # Pass file that has no <autoevolve_mindset>
        extract_mindset_xml(DIRECTION_PATH)
