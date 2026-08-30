"""Unit and integration test suite for AutoEvolve v3.0/v4.0 evidence inheritance features."""
from __future__ import annotations

import os
import shutil
import tempfile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from benchmarks.harness.skeptic_auditor import (
    audit_test_assertion_rigor,
    audit_dig_contract,
    audit_evidence_ladder,
    run_skeptic_audit,
)
from scripts.lineage import generate_lineage_mermaid


@pytest.fixture
def temp_workspace():
    tmp = tempfile.mkdtemp(prefix="autoevolve_praxist_test_")
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


class TestSkepticAuditor:
    def test_rigorous_test_file(self, temp_workspace):
        test_file = os.path.join(temp_workspace, "test_sample.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("""
def test_addition():
    assert 2 + 2 == 4
    assert 3 * 3 == 9
""")
        res = audit_test_assertion_rigor(test_file)
        assert res["file_exists"] is True
        assert res["assert_count"] == 2
        assert res["trivial_asserts"] == 0
        assert res["rigor_score"] == 1.0
        assert res["skeptic_approved"] is True

    def test_tampered_test_file_assert_true(self, temp_workspace):
        test_file = os.path.join(temp_workspace, "test_weak.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("""
def test_fake_pass():
    assert True
""")
        res = audit_test_assertion_rigor(test_file)
        assert res["file_exists"] is True
        assert res["trivial_asserts"] == 1
        assert res["rigor_score"] < 1.0
        assert res["skeptic_approved"] is False
        assert any("Trivial assertion" in v for v in res["violations"])

    def test_dig_contract_audit_valid(self):
        contract = """
        <innovation_contract>
          - Target Hypothesis: Hoisting compiled regex lowers search p99.
          - Surface: `src/search.py:match_pattern`
          - Intent: exploit
          - Expected Evidence: p99 latency < 90ms with 0 errors
          - Anti-Goals: No unbounded heap cache, no global mutable locks.
        </innovation_contract>
        """
        res = audit_dig_contract(contract)
        assert res["has_contract"] is True
        assert res["skeptic_approved"] is True
        assert res["score"] == 1.0

    def test_dig_contract_audit_empty_reject(self):
        res = audit_dig_contract("")
        assert res["has_contract"] is False
        assert res["skeptic_approved"] is False

    def test_evidence_ladder_eval_smoke_pass(self):
        res = audit_evidence_ladder(["smoke", "scout", "complete"])
        assert res["staged"] is True
        assert res["score"] == 1.0
        assert res["skeptic_approved"] is True

    def test_evidence_ladder_eval_smoke_only(self):
        res = audit_evidence_ladder(["smoke"])
        assert res["staged"] is True
        assert res["score"] == 0.2
        assert res["skeptic_approved"] is False


class TestToolingScripts:
    def test_contract_validator_execution(self, temp_workspace):
        contract_file = os.path.join(temp_workspace, "contract.md")
        with open(contract_file, "w", encoding="utf-8") as f:
            f.write("""
<innovation_contract>
  - Target Hypothesis: Indexing key
  - Surface: `db.py`
  - Intent: explore
  - Expected Evidence: speedup
  - Anti-Goals: none
</innovation_contract>
""")
        res = audit_dig_contract(open(contract_file).read())
        assert res["has_contract"] is True
        assert res["skeptic_approved"] is True

    def test_lineage_dag_generation(self, temp_workspace):
        entries = [
            {"commit": "HEAD~0", "signal": "10 passed", "decision": "BASELINE", "description": "Base"},
            {"commit": "e4f1a2", "signal": "88ms", "decision": "KEEP", "description": "Hoisted regex"},
            {"commit": "------", "signal": "Deadlock", "decision": "REVERT", "description": "Global lock contention"},
            {"commit": "a8c9d1", "signal": "42ms", "decision": "KEEP", "description": "Compound index"},
        ]
        mermaid = generate_lineage_mermaid(entries)
        assert "graph TD" in mermaid
        assert 'Base["Baseline HEAD"]' in mermaid
        assert "Hoisted regex" in mermaid
        assert "Falsified" in mermaid
        assert "Compound index" in mermaid

    def test_agents_md_integrity(self):
        worktree_agents = os.path.abspath(os.path.join(REPO_ROOT, "AutoEvolve", "AGENTS.md"))
        with open(worktree_agents, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Deep Innovation Gate (DIG)" in content
        assert "Staged Verification" in content
        assert "CONSTRAINTS.md" in content
        assert "Gems Memory Compression" in content
        assert "Adversarial Skeptic self-audit" in content
        assert "Provenance & Lineage" in content
