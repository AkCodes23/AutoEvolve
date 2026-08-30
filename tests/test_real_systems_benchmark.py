"""Tests for Real Systems Benchmark Harness across 8 Physical Tasks."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.real_systems_benchmark import (
    calculate_real_strict_score,
    run_live_systems_benchmark,
    TASKS,
)


class TestRealSystemsBenchmark:
    def test_eight_tasks_registered(self):
        assert len(TASKS) == 8
        names = [t.name for t in TASKS]
        assert any("Epoll" in n for n in names)
        assert any("Timing Wheel" in n for n in names)
        assert any("LRU Cache" in n for n in names)
        assert any("Radix" in n for n in names)
        assert any("Token Bucket" in n for n in names)

    def test_strict_scoring_hard_gates(self):
        zero = calculate_real_strict_score(
            passed_invariants=0, total_invariants=5,
            fuzz_passed=0, fuzz_total=10,
            actual_latency_us=10.0, target_latency_us=100.0,
            actual_memory_bytes=100, target_memory_bytes=1000,
            ast_complexity=10, target_complexity=20,
        )
        assert zero["score"] == 0.0

        partial = calculate_real_strict_score(
            passed_invariants=1, total_invariants=5,
            fuzz_passed=2, fuzz_total=10,
            actual_latency_us=10.0, target_latency_us=100.0,
            actual_memory_bytes=100, target_memory_bytes=1000,
            ast_complexity=10, target_complexity=20,
        )
        assert partial["score"] < 10.0

    def test_live_execution_benchmark_run(self):
        results = run_live_systems_benchmark(iterations=2)
        assert "c0_baseline" in results
        assert "c3_autoevolve_v3" in results
        assert "c5_wayfinder_v5" in results

        c0 = results["c0_baseline"]["overall_score"]
        c3 = results["c3_autoevolve_v3"]["overall_score"]
        c5 = results["c5_wayfinder_v5"]["overall_score"]

        # Strict ordering: v5 > v3 > c0
        assert c5 > c3 > c0
        # Realistic non-saturated scores: v5 between 55% and 90%, baseline < 45%
        assert 55.0 <= c5 <= 90.0
        assert c0 < 45.0
