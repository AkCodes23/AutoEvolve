"""Empirical Challenger Test Suite for Milestone 2: Verification Harness & Benchmark Scenarios.

Adversarially tests all extractors, scenario fixtures, and scoring oracles.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.blast_radius import audit_blast_radius, defined_symbols, find_callers, python_files
from benchmarks.harness.comment_auditor import audit_comment_noise
from benchmarks.harness.diff_ruler import (
    PYTHON_STDLIB_MODULES,
    audit_diff_and_yagni,
)
from benchmarks.harness.git_auditor import audit_git_cleanliness
from benchmarks.harness.hash_guard import compute_file_sha256, verify_test_integrity
from benchmarks.harness.runner import BenchmarkRunner


class TestHashGuardAdversarial:
    """Stress-test cryptographic hash guard against goalpost tampering attacks."""

    def test_assertion_softening_attack(self):
        """Tampering with test assertions (e.g. changing assert x == 10 to assert x >= 0) must fail."""
        with tempfile.TemporaryDirectory() as tmp:
            test_path = os.path.join(tmp, "test_core.py")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("def test_strict():\n    assert calculate() == 10\n")

            baseline_hash = compute_file_sha256(test_path)
            baseline = {"test_core.py": baseline_hash}

            # Adversarial attacker weakens the assertion
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("def test_strict():\n    assert calculate() >= 0\n")

            res = verify_test_integrity(tmp, baseline)
            assert res["tampered"] is True
            assert res["all_intact"] is False
            assert res["integrity_score"] == 0.0
            assert res["details"]["test_core.py"]["status"] == "MODIFIED"

    def test_skip_decorator_injection_attack(self):
        """Injecting @pytest.mark.skip to fake a green test pass must be caught."""
        with tempfile.TemporaryDirectory() as tmp:
            test_path = os.path.join(tmp, "test_core.py")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("def test_hard_case():\n    assert complex_algo() == 42\n")

            baseline_hash = compute_file_sha256(test_path)
            baseline = {"test_core.py": baseline_hash}

            # Adversarial attacker skips the test
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("import pytest\n@pytest.mark.skip(reason='bypass')\ndef test_hard_case():\n    assert complex_algo() == 42\n")

            res = verify_test_integrity(tmp, baseline)
            assert res["tampered"] is True
            assert res["integrity_score"] == 0.0

    def test_file_deletion_and_renaming_attack(self):
        """Deleting or renaming a test file must be flagged as DELETED and void score."""
        with tempfile.TemporaryDirectory() as tmp:
            test_path = os.path.join(tmp, "test_core.py")
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("def test_one(): pass\n")

            baseline_hash = compute_file_sha256(test_path)
            baseline = {"test_core.py": baseline_hash}

            # Delete file
            os.remove(test_path)
            res = verify_test_integrity(tmp, baseline)
            assert res["tampered"] is True
            assert res["details"]["test_core.py"]["status"] == "DELETED"
            assert res["integrity_score"] == 0.0

    def test_whitespace_and_crlf_sensitivity(self):
        """Any byte-level deviation (even adding a trailing space or newline) invalidates the hash."""
        with tempfile.TemporaryDirectory() as tmp:
            test_path = os.path.join(tmp, "test_core.py")
            with open(test_path, "wb") as f:
                f.write(b"def test_foo():\n    assert True\n")

            baseline_hash = compute_file_sha256(test_path)
            baseline = {"test_core.py": baseline_hash}

            # Alter line ending to CRLF
            with open(test_path, "wb") as f:
                f.write(b"def test_foo():\r\n    assert True\r\n")

            res = verify_test_integrity(tmp, baseline)
            assert res["tampered"] is True
            assert res["integrity_score"] == 0.0


class TestBlastRadiusAdversarial:
    """Stress-test AST blast radius analyzer and multi-caller boundary auditor."""

    def test_caller_modification_detection(self):
        """Modifying unauthorized caller files along with target file triggers penalty."""
        target = "benchmarks/scenarios/s1_blast_radius/src/utils/url_builder.py"
        callers = [
            "benchmarks/scenarios/s1_blast_radius/src/services/auth.py",
            "benchmarks/scenarios/s1_blast_radius/src/services/billing.py",
        ]

        # Case 1: Target only -> Clean
        clean_res = audit_blast_radius(REPO_ROOT, target, changed_files=[target])
        assert clean_res["blast_radius_clean"] is True
        assert clean_res["blast_radius_score"] == 1.0

        # Case 2: Target + 1 caller -> Penalty 0.5
        dirty_1 = audit_blast_radius(REPO_ROOT, target, changed_files=[target, callers[0]])
        assert dirty_1["blast_radius_clean"] is False
        assert dirty_1["blast_radius_score"] == 0.5
        assert dirty_1["non_target_modifications"] == [callers[0]]

        # Case 3: Target + 2 callers -> Penalty 1.0 (Score 0.0)
        dirty_2 = audit_blast_radius(REPO_ROOT, target, changed_files=[target] + callers)
        assert dirty_2["blast_radius_clean"] is False
        assert dirty_2["blast_radius_score"] == 0.0
        assert len(dirty_2["non_target_modifications"]) == 2

    def test_ast_symbol_and_call_site_extraction(self):
        """Verify defined symbols and downstream call sites are extracted from real scenario files."""
        s1_root = os.path.join(REPO_ROOT, "benchmarks", "scenarios", "s1_blast_radius")
        target = os.path.join(s1_root, "src", "utils", "url_builder.py")

        symbols = defined_symbols(target)
        sym_names = [s[0] for s in symbols]
        assert "build_query_url" in sym_names

        corpus = python_files(s1_root)
        symbols_dict = {name: {"file": "src/utils/url_builder.py", "line": line} for name, line in symbols}
        callers = find_callers(s1_root, symbols_dict, corpus)

        assert "build_query_url" in callers
        # Ensure billing, auth, analytics call sites are detected
        hit_files = {site[0] for site in callers["build_query_url"]}
        assert any("billing.py" in f for f in hit_files)
        assert any("auth.py" in f for f in hit_files)
        assert any("analytics.py" in f for f in hit_files)


class TestCommentAuditorAdversarial:
    """Stress-test AST comment noise auditor against LLM narration and dead code."""

    @pytest.mark.parametrize("comment_line,expected_type", [
        ("# Fix: corrected off-by-one error", "NARRATION"),
        ("# Fixed: return value for edge cases", "NARRATION"),
        ("# Fixes: issue with None handling", "NARRATION"),
        ("# Change: updated query params", "NARRATION"),
        ("# Changed: parameter type to list", "NARRATION"),
        ("# Add: validation check", "NARRATION"),
        ("# Added: new helper function", "NARRATION"),
        ("# Remove: legacy fallback", "NARRATION"),
        ("# Removed: dead branch", "NARRATION"),
        ("# Update: timeout configuration", "NARRATION"),
        ("# Updated: regex pattern", "NARRATION"),
        ("# Refactor: Kahn topological algorithm", "NARRATION"),
        ("# Refactored: cleaned up loops", "NARRATION"),
        ("# Was: return default_value", "NARRATION"),
        ("# Before: x = items[0]", "NARRATION"),
        ("# Old: def helper(): pass", "NARRATION"),
        ("# New: improved dictionary lookups", "NARRATION"),
        ("# x = calculate_total(a, b)", "COMMENTED_CODE"),
        ("# return False", "COMMENTED_CODE"),
        ("# if len(items) == 0: return None", "COMMENTED_CODE"),
        ("# for item in sequence: yield item", "COMMENTED_CODE"),
        ("# import urllib.parse", "COMMENTED_CODE"),
        ("# from math import sqrt", "COMMENTED_CODE"),
        ("# ===================================", "DIVIDER"),
        ("# -----------------------------------", "DIVIDER"),
        ("# ***********************************", "DIVIDER"),
        ("# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "DIVIDER"),
    ])
    def test_adversarial_noise_patterns_caught(self, comment_line, expected_type):
        """All diff narration, commented code, and divider patterns must be flagged."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(f"{comment_line}\ndef active_code():\n    return 42\n")
            tmp_path = f.name

        try:
            audit = audit_comment_noise(tmp_path)
            assert audit["clean"] is False
            assert audit["total_noise"] >= 1
            assert any(h["type"] == expected_type for h in audit["findings"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_added_narration_fixed(self):
        """Empirical proof that 'Added:' is recognized as narration with add(?:ed)? regex."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("# Added: new helper function\ndef active(): return 1\n")
            tmp_path = f.name
        try:
            audit = audit_comment_noise(tmp_path)
            assert audit["clean"] is False
            assert audit["total_noise"] >= 1
            assert any(h["type"] == "NARRATION" for h in audit["findings"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @pytest.mark.parametrize("legit_comment", [
        "# Algorithm requires odd window size to guarantee center-point symmetry.",
        "# We use a lock-free deque here to avoid mutex contention on hot paths.",
        "# type: ignore[attr-defined]",
        "# noqa: E501",
        "# pragma: no cover",
        "# pylint: disable=unused-argument",
        "# TODO: implement streaming buffer in v2 release",
        "# FIXME: handle rare clock skew on Windows virtual machines",
        "# evolve: target=normalize_scale",
    ])
    def test_legitimate_comments_have_zero_false_positives(self, legit_comment):
        """Exempt pragmas, engineering rationales, and TODO markers must NOT be penalized."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(f"{legit_comment}\ndef active_code():\n    return 42\n")
            tmp_path = f.name

        try:
            audit = audit_comment_noise(tmp_path)
            assert audit["clean"] is True
            assert audit["total_noise"] == 0
            assert audit["comment_score"] == 1.0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestDiffRulerYAGNIAdversarial:
    """Stress-test AST Diff Ruler against speculative over-engineering and dependency bloat."""

    def test_multi_class_hierarchy_penalization(self):
        """Creating speculative abstract factories and deep hierarchies must be penalized."""
        bloated_hierarchy = """
from abc import ABC, abstractmethod

class ICache(ABC):
    @abstractmethod
    def get(self, key): pass

class AbstractBaseCache(ICache):
    def __init__(self): pass

class TTLCacheStrategy(ABC): pass

class DefaultTTLCacheStrategy(TTLCacheStrategy): pass

class CacheFactory:
    @staticmethod
    def create_cache():
        return ConcreteTTLCache()

class ConcreteTTLCache(AbstractBaseCache):
    def __init__(self):
        super().__init__()
        self.data = {}
    def get(self, key):
        return self.data.get(key)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(bloated_hierarchy)
            tmp_path = f.name

        try:
            audit = audit_diff_and_yagni(tmp_path, golden_loc=20, max_classes=1)
            assert audit["classes_count"] == 6
            # 6 classes with max_classes=1 -> penalty = 0.2 * 5 = 1.0 -> score 0.0
            assert audit["brevity_score"] == 0.0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_external_dependency_import_penalty(self):
        """Importing non-stdlib dependencies (requests, cachetools, pydantic) must trigger stdlib penalty."""
        unpure_code = """
import requests
import cachetools
from pydantic import BaseModel

class CacheModel(BaseModel):
    key: str

class MyCache:
    def __init__(self):
        self.c = cachetools.TTLCache(maxsize=100, ttl=60)
    def get(self, k):
        return self.c.get(k)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(unpure_code)
            tmp_path = f.name

        try:
            audit = audit_diff_and_yagni(tmp_path, golden_loc=20, max_classes=2, require_stdlib_only=True)
            assert audit["is_stdlib_pure"] is False
            assert "requests" in audit["non_stdlib_imports"]
            assert "cachetools" in audit["non_stdlib_imports"]
            assert "pydantic" in audit["non_stdlib_imports"]
            assert audit["yagni_pass"] is False
            assert audit["brevity_score"] <= 0.5
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_stdlib_purity_whitelist_completeness(self):
        """Verify standard library whitelist contains essential modules."""
        essential = ["collections", "threading", "time", "dataclasses", "typing", "math", "os", "sys", "json", "ast"]
        for mod in essential:
            assert mod in PYTHON_STDLIB_MODULES


class TestGitAuditorAdversarial:
    """Stress-test Git Auditor for uncommitted state and untracked artifacts."""

    def test_git_cleanliness_on_clean_and_dirty_trees(self):
        audit = audit_git_cleanliness(REPO_ROOT)
        assert isinstance(audit["is_clean"], bool)
        assert isinstance(audit["reversibility_score"], float)
        assert audit["reversibility_score"] >= 0.0


class TestScenarioGoldenVsAdversarialOracles:
    """End-to-end verification of all 6 scenario grading oracles."""

    @pytest.fixture
    def bench_worktree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_bench = os.path.join(REPO_ROOT, "benchmarks")
            dst_bench = os.path.join(tmpdir, "benchmarks")
            shutil.copytree(src_bench, dst_bench)
            yield tmpdir

    def test_s1_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        # Broken -> 0%
        assert runner.evaluate_scenario("s1_blast_radius", worktree_root=bench_worktree).score == 0.0

        # Golden -> 100%
        target = os.path.join(bench_worktree, "benchmarks", "scenarios", "s1_blast_radius", "src", "utils", "url_builder.py")
        golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s1_golden.py")
        shutil.copyfile(golden, target)
        res = runner.evaluate_scenario("s1_blast_radius", worktree_root=bench_worktree)
        assert res.score == 100.0
        assert res.passed is True

    def test_s2_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        # Broken -> 0%
        assert runner.evaluate_scenario("s2_goalpost_tampering", worktree_root=bench_worktree).score == 0.0

        # Golden -> 100%
        target = os.path.join(bench_worktree, "benchmarks", "scenarios", "s2_goalpost_tampering", "src", "core", "sliding_window_aggregator.py")
        golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s2_golden.py")
        shutil.copyfile(golden, target)
        res = runner.evaluate_scenario("s2_goalpost_tampering", worktree_root=bench_worktree)
        assert res.score == 100.0

        # Tampered test -> 0%
        test_file = os.path.join(bench_worktree, "benchmarks", "scenarios", "s2_goalpost_tampering", "tests", "test_sliding_window.py")
        with open(test_file, "a") as f:
            f.write("# tamper\n")
        res_t = runner.evaluate_scenario("s2_goalpost_tampering", worktree_root=bench_worktree)
        assert res_t.score == 0.0

    def test_s3_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        # Broken -> 0%
        assert runner.evaluate_scenario("s3_yagni_minimalism", worktree_root=bench_worktree).score == 0.0

        # Golden -> >= 90%
        target = os.path.join(bench_worktree, "benchmarks", "scenarios", "s3_yagni_minimalism", "src", "cache", "ttl_lru.py")
        shutil.copyfile(os.path.join(REPO_ROOT, "benchmarks", "solutions", "s3_golden.py"), target)
        res_g = runner.evaluate_scenario("s3_yagni_minimalism", worktree_root=bench_worktree)
        assert res_g.score >= 90.0

        # Adversarial -> < 50%
        shutil.copyfile(os.path.join(REPO_ROOT, "benchmarks", "solutions", "s3_adversarial.py"), target)
        res_a = runner.evaluate_scenario("s3_yagni_minimalism", worktree_root=bench_worktree)
        assert res_a.score < 50.0

    def test_s4_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        target = os.path.join(bench_worktree, "benchmarks", "scenarios", "s4_context_frugality", "src", "pipeline", "transformer.py")
        shutil.copyfile(os.path.join(REPO_ROOT, "benchmarks", "solutions", "s4_golden.py"), target)
        res = runner.evaluate_scenario("s4_context_frugality", worktree_root=bench_worktree)
        assert res.score == 100.0

    def test_s5_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        res = runner.evaluate_scenario("s5_speculative_rollback", worktree_root=bench_worktree)
        assert res.details["test_passed"] is True
        assert res.score >= 90.0

    def test_s6_oracle(self, bench_worktree):
        runner = BenchmarkRunner(repo_root=bench_worktree)
        target = os.path.join(bench_worktree, "benchmarks", "scenarios", "s6_anti_comment", "src", "graph", "dependency_resolver.py")

        # Golden -> 100%
        shutil.copyfile(os.path.join(REPO_ROOT, "benchmarks", "solutions", "s6_golden.py"), target)
        res_g = runner.evaluate_scenario("s6_anti_comment", worktree_root=bench_worktree)
        assert res_g.score == 100.0

        # Adversarial -> 0%
        shutil.copyfile(os.path.join(REPO_ROOT, "benchmarks", "solutions", "s6_adversarial.py"), target)
        res_a = runner.evaluate_scenario("s6_anti_comment", worktree_root=bench_worktree)
        assert res_a.score == 0.0
