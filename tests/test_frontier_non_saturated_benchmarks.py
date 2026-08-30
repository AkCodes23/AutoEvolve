"""Tests for the Frontier Non-Saturated SWE Benchmark Suite."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.frontier_engine import calculate_continuous_score
from benchmarks.frontier_benchmark import FRONTIER_TASKS, evaluate_frontier_matrix


class TestFrontierContinuousEngine:
    def test_continuous_score_scaling_and_penalty(self):
        # Perfect run
        perfect = calculate_continuous_score(
            correctness_rate=1.0,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=50,
            golden_loc=50,
            concurrency_errors=0,
        )
        assert perfect["score"] == 100.0

        # Memory blowup penalty (10x memory)
        mem_blowup = calculate_continuous_score(
            correctness_rate=1.0,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=10240,
            target_memory_kb=1024,
            actual_loc=50,
            golden_loc=50,
            concurrency_errors=0,
        )
        assert mem_blowup["score"] < perfect["score"]
        assert mem_blowup["memory_score"] <= 10.0

        # Concurrency penalty
        race_bugs = calculate_continuous_score(
            correctness_rate=1.0,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=50,
            golden_loc=50,
            concurrency_errors=4,
        )
        assert race_bugs["safety_score"] == 0.0
        assert race_bugs["score"] < perfect["score"]

        # Catastrophic correctness drop (gating factor)
        broken = calculate_continuous_score(
            correctness_rate=0.2,
            actual_latency_ms=10.0,
            target_latency_ms=10.0,
            actual_memory_kb=1024,
            target_memory_kb=1024,
            actual_loc=50,
            golden_loc=50,
            concurrency_errors=0,
        )
        assert broken["score"] < 25.0

    def test_10_frontier_tasks_configured(self):
        assert len(FRONTIER_TASKS) == 10
        total_weight = sum(t["weight"] for t in FRONTIER_TASKS)
        assert abs(total_weight - 1.0) < 0.01

    def test_frontier_matrix_evaluation_spread(self):
        res = evaluate_frontier_matrix()
        summary = res["summary"]
        assert summary["c0_baseline"] < 20.0
        assert summary["c1_karpathy"] < 65.0
        assert summary["c2_ponytail"] < 80.0
        assert summary["c3_autoevolve_v2"] < 92.0
        assert summary["c5_autoevolve_praxist"] > 95.0
        # Verified clear non-saturated separation across all 5 conditions
        assert summary["c0_baseline"] < summary["c1_karpathy"] < summary["c2_ponytail"] < summary["c3_autoevolve_v2"] < summary["c5_autoevolve_praxist"]
