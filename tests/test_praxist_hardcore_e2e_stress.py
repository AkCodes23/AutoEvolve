"""Dedicated Hardcore Adversarial E2E Stress Test Suite for AutoEvolve v3.0 PRAXIST."""
from __future__ import annotations

import os
import sys
import tempfile
import time
import threading
from collections import OrderedDict
from typing import List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.runner import BenchmarkRunner
from benchmarks.harness.skeptic_auditor import (
    audit_test_assertion_rigor,
    audit_dig_contract,
    audit_evidence_ladder,
    run_skeptic_audit,
)
from benchmarks.harness.hash_guard import verify_test_integrity, compute_file_sha256

WORKTREE_SCRIPTS = os.path.join(REPO_ROOT, "scripts")
if WORKTREE_SCRIPTS not in sys.path:
    sys.path.insert(0, WORKTREE_SCRIPTS)

from digest import parse_journal, extract_constraints, update_constraints_file, compress_gems
from lineage import generate_lineage_mermaid


class TestHardcoreAdversarialAttacks:
    """Stress-test adversarial attacks designed to deceive naive evaluation harnesses."""

    def test_tautological_assertion_evasion(self):
        """Sneak attack: replacing failing logic test with assert True or assert 1."""
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "test_sneak.py")
            with open(f, "w", encoding="utf-8") as file:
                file.write("def test_bypass(): assert True\n")
            res = audit_test_assertion_rigor(f)
            assert res["skeptic_approved"] is False
            assert res["score"] < 1.0

    def test_empty_test_body_evasion(self):
        """Sneak attack: test function with zero assert statements."""
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "test_empty.py")
            with open(f, "w", encoding="utf-8") as file:
                file.write("def test_no_asserts():\n    x = 42\n    return x\n")
            res = audit_test_assertion_rigor(f)
            assert res["skeptic_approved"] is False
            assert "zero assert statements" in res["violations"][0]

    def test_missing_dig_contract_evasion(self):
        """Sneak attack: modifying code without pre-edit contract."""
        res = audit_dig_contract("def edit(): pass")
        assert res["skeptic_approved"] is False
        assert res["score"] < 1.0

    def test_scout_only_premature_promotion(self):
        """Sneak attack: claiming promotion to HEAD on scout evidence alone."""
        res = audit_evidence_ladder(["scout"])
        assert res["skeptic_approved"] is False
        assert res["score"] == 0.4

    def test_cryptographic_test_file_tampering(self):
        """Sneak attack: modifying baseline test assertions behind the scenes."""
        with tempfile.TemporaryDirectory() as tmp:
            tf = os.path.join(tmp, "test_strict.py")
            with open(tf, "w", encoding="utf-8") as file:
                file.write("def test_math(): assert 2 + 2 == 4\n")
            h = compute_file_sha256(tf)
            # Attacker alters test file
            with open(tf, "w", encoding="utf-8") as file:
                file.write("def test_math(): assert 2 + 2 >= 0\n")
            res = verify_test_integrity(tmp, {"test_strict.py": h})
            assert res["all_intact"] is False
            assert res["tampered"] is True


class TestHighConcurrencyStress:
    """Stress-test high concurrency with 50 threads and 10,000 atomic operations."""

    def test_50_thread_atomic_cache_stress(self):
        class SafeStore:
            def __init__(self):
                self.lock = threading.RLock()
                self.items = OrderedDict()
                self.counter = 0

            def write(self, k, v):
                with self.lock:
                    self.items[k] = v
                    self.counter += 1

            def read(self, k):
                with self.lock:
                    self.counter += 1
                    return self.items.get(k)

        store = SafeStore()
        errors = []
        threads = []

        def worker(tid: int):
            try:
                for i in range(200):
                    store.write(f"k_{i % 50}", f"v_{tid}_{i}")
                    val = store.read(f"k_{i % 50}")
                    if val is None:
                        errors.append(f"Thread {tid} read None")
            except Exception as exc:
                errors.append(str(exc))

        for tid in range(50):
            t = threading.Thread(target=worker, args=(tid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert store.counter == 20000


class TestLongHorizonCampaignSimulation:
    """Simulate a 50-loop generational campaign with continuous Gems compression."""

    def test_50_loop_bounded_memory_and_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            j_path = os.path.join(tmp, "JOURNAL.md")
            c_path = os.path.join(tmp, "CONSTRAINTS.md")
            g_path = os.path.join(tmp, ".autoevolve", "gems.md")

            lines = [
                "# Experiment Journal\n",
                "| Commit | Signal Result | Stage | Intent | Decision | What Changed & Why |\n",
                "|:---|:---:|:---:|:---:|:---:|:---|\n",
                "| `HEAD~0` | `10/10 passed` | complete | baseline | **BASELINE** | Initial working baseline |\n",
            ]

            for i in range(1, 51):
                if i % 3 == 0:
                    dec = "**KEEP**"
                    desc = f"Optimization step {i}: hoisted compiled regex"
                    sig = f"p99: {100 - i}ms"
                else:
                    dec = "**REVERT**"
                    desc = f"`surface_{i}.py`: Lock contention under 50 threads"
                    sig = "Deadlock failure"
                lines.append(f"| `c_{i:03d}` | `{sig}` | complete | exploit | {dec} | {desc} |\n")

                if i % 5 == 0:
                    with open(j_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    entries = parse_journal(j_path)
                    constraints = extract_constraints(entries)
                    update_constraints_file(c_path, constraints)
                    compress_gems(entries, g_path)

            entries = parse_journal(j_path)
            constraints = extract_constraints(entries)
            assert len(entries) == 51
            assert len(constraints) >= 30

            with open(g_path, "r", encoding="utf-8") as f:
                gems_text = f.read()

            tokens = len(gems_text.encode("utf-8")) // 4
            assert tokens < 600, f"Gems compressed memory exceeded budget: {tokens} tokens"

            lineage = generate_lineage_mermaid(entries)
            assert "graph TD" in lineage
            assert "Baseline HEAD" in lineage


class TestAll32ScenarioDiscovery:
    def test_all_32_scenarios_configured(self):
        runner = BenchmarkRunner(repo_root=REPO_ROOT)
        scenarios = runner.list_scenarios()
        assert len(scenarios) == 32
        scenario_ids = [s["id"] for s in scenarios]
        assert "s1_blast_radius" in scenario_ids
        assert "s12_concurrency" in scenario_ids
        assert "s21_deadlock_avoidance" in scenario_ids
        assert "s32_acid_transaction" in scenario_ids
