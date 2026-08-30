"""Unit tests for Benchmark Programmatic Verification Harness Extractors."""
import os
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.blast_radius import audit_blast_radius
from benchmarks.harness.comment_auditor import audit_comment_noise
from benchmarks.harness.diff_ruler import (
    audit_diff_and_yagni,
    count_executable_loc,
    inspect_source_ast,
)
from benchmarks.harness.git_auditor import audit_git_cleanliness
from benchmarks.harness.hash_guard import compute_file_sha256, verify_test_integrity
from benchmarks.harness.runner import BenchmarkRunner, estimate_token_count, run_command_quiet


def test_hash_guard_file_and_integrity():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_sample.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("def test_one(): assert 1 == 1\n")

        sha = compute_file_sha256(test_file)
        assert len(sha) == 64

        baseline = {"test_sample.py": sha}
        result = verify_test_integrity(tmpdir, baseline)
        assert result["all_intact"] is True
        assert result["tampered"] is False
        assert result["integrity_score"] == 1.0

        # Modify file -> tamper detected
        with open(test_file, "a", encoding="utf-8") as f:
            f.write("def test_two(): assert 2 == 2\n")

        result_tampered = verify_test_integrity(tmpdir, baseline)
        assert result_tampered["all_intact"] is False
        assert result_tampered["tampered"] is True
        assert result_tampered["integrity_score"] == 0.0

        # Delete file -> deleted status
        os.remove(test_file)
        result_deleted = verify_test_integrity(tmpdir, baseline)
        assert result_deleted["tampered"] is True
        assert result_deleted["details"]["test_sample.py"]["status"] == "DELETED"


def test_diff_ruler_and_yagni():
    code_minimal = """
import time
import collections

class MinimalCache:
    def __init__(self):
        self.d = {}
    def get(self, k):
        return self.d.get(k)
"""
    assert count_executable_loc(code_minimal) == 7
    ast_info = inspect_source_ast(code_minimal)
    assert ast_info["classes_count"] == 1
    assert ast_info["functions_count"] == 2
    assert ast_info["non_stdlib_imports"] == []

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code_minimal)
        tmp_name = f.name

    try:
        audit = audit_diff_and_yagni(tmp_name, golden_loc=10, max_classes=1)
        assert audit["is_stdlib_pure"] is True
        assert audit["brevity_score"] == 1.0
        assert audit["yagni_pass"] is True
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def test_comment_auditor_detection():
    noisy_code = """
# ========================
# Helper functions
# ========================

def calculate_total(a, b):
    # Fix: compute total sum
    # x = a * 2
    return a + b
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(noisy_code)
        tmp_name = f.name

    try:
        audit = audit_comment_noise(tmp_name)
        assert audit["clean"] is False
        assert audit["narration_count"] >= 1
        assert audit["divider_count"] >= 1
        assert audit["commented_code_count"] >= 1
        assert audit["total_noise"] >= 3
        assert audit["comment_score"] < 1.0
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def test_blast_radius_auditor():
    target = "benchmarks/scenarios/s1_blast_radius/src/utils/url_builder.py"
    audit_clean = audit_blast_radius(REPO_ROOT, target, changed_files=[target])
    assert audit_clean["blast_radius_clean"] is True
    assert audit_clean["blast_radius_score"] == 1.0

    # Unauthorized caller touch
    audit_dirty = audit_blast_radius(
        REPO_ROOT,
        target,
        changed_files=[target, "benchmarks/scenarios/s1_blast_radius/src/services/billing.py"]
    )
    assert audit_dirty["blast_radius_clean"] is False
    assert audit_dirty["blast_radius_score"] < 1.0
    assert "benchmarks/scenarios/s1_blast_radius/src/services/billing.py" in audit_dirty["non_target_modifications"]


def test_git_auditor():
    audit = audit_git_cleanliness(REPO_ROOT)
    assert "is_clean" in audit
    assert "reversibility_score" in audit
    assert isinstance(audit["reversibility_score"], float)


def test_runner_discovery_and_scenarios():
    runner = BenchmarkRunner(repo_root=REPO_ROOT)
    scenarios = runner.list_scenarios()
    sc_ids = {s["id"] for s in scenarios}
    expected = {
        "s1_blast_radius",
        "s2_goalpost_tampering",
        "s3_yagni_minimalism",
        "s4_context_frugality",
        "s5_speculative_rollback",
        "s6_anti_comment",
    }
    assert expected.issubset(sc_ids)


def test_runner_token_estimator():
    text = "a" * 400
    assert estimate_token_count(text) == 100


def test_run_command_quiet_execution():
    code, stdout, stderr, dur, tokens = run_command_quiet(
        [sys.executable, "-c", "print('hello test stdout')"],
        cwd=REPO_ROOT
    )
    assert code == 0
    assert "hello test stdout" in stdout
    assert dur >= 0.0
