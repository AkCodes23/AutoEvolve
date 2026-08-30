"""Tests for the Multi-Benchmark Unified Matrix (v3.0 vs v3.5 vs v4.0)."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.multi_benchmark_matrix import BENCHMARK_SUITES, run_multi_benchmark_matrix


class TestMultiBenchmarkSuite:
    def test_all_5_benchmark_suites_configured(self):
        assert len(BENCHMARK_SUITES) == 5
        total_weight = sum(s["weight"] for s in BENCHMARK_SUITES)
        assert abs(total_weight - 1.0) < 0.01

    def test_multi_benchmark_matrix_execution(self):
        res = run_multi_benchmark_matrix()
        summary = res["summary"]
        assert summary["c0_baseline"] < 15.0
        assert summary["c1_karpathy"] < 35.0
        assert summary["c2_ponytail"] < 50.0
        assert summary["c3_autoevolve_v2"] < 70.0
        assert summary["c5_praxist_v3"] >= 80.0
        assert summary["c6_lats_prm_v35"] >= 85.0
        assert summary["c7_swarm_v40"] >= 92.0
        # Strict monotonic progression verified across all 7 milestones
        assert (
            summary["c0_baseline"]
            < summary["c1_karpathy"]
            < summary["c2_ponytail"]
            < summary["c3_autoevolve_v2"]
            < summary["c5_praxist_v3"]
            < summary["c6_lats_prm_v35"]
            < summary["c7_swarm_v40"]
        )
