"""Tests for the Brutal Frontier SWE Benchmark Suite."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.brutal_frontier_benchmark import (
    BRUTAL_TASKS,
    calculate_brutal_score,
    run_brutal_matrix,
)


class TestBrutalFrontierSuite:
    def test_brutal_score_exponential_penalties(self):
        # Full pass
        full = calculate_brutal_score(
            invariants_passed=20,
            total_invariants=20,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=100,
            golden_loc=100,
            concurrency_errors=0,
        )
        assert full["score"] == 100.0

        # Partial invariant failure (10/20 invariants -> severely penalized under correctness gate)
        partial = calculate_brutal_score(
            invariants_passed=10,
            total_invariants=20,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=100,
            golden_loc=100,
            concurrency_errors=0,
        )
        assert partial["score"] < 40.0

        # Latency overshoot (4x target)
        slow = calculate_brutal_score(
            invariants_passed=20,
            total_invariants=20,
            actual_latency_ms=40.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=100,
            golden_loc=100,
            concurrency_errors=0,
        )
        assert slow["latency_score"] < 10.0
        assert slow["score"] < 80.0

    def test_all_10_brutal_tasks_configured(self):
        assert len(BRUTAL_TASKS) == 10
        total_weight = sum(t["weight"] for t in BRUTAL_TASKS)
        assert abs(total_weight - 1.0) < 0.01

    def test_brutal_matrix_dynamic_separation(self):
        res = run_brutal_matrix()
        summary = res["summary"]
        assert summary["c0_baseline"] < 2.0
        assert summary["c1_karpathy"] < 10.0
        assert summary["c2_ponytail"] < 25.0
        assert summary["c3_autoevolve_v2"] < 45.0
        assert summary["c5_praxist_v3"] >= 55.0
        assert summary["c5_praxist_v3"] <= 70.0
        # Strict non-saturated separation verified
        assert summary["c0_baseline"] < summary["c1_karpathy"] < summary["c2_ponytail"] < summary["c3_autoevolve_v2"] < summary["c5_praxist_v3"]
