"""Tests for Multi-Benchmark Unified Suite (Strict Non-Saturated)."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.multi_benchmark_matrix import BENCHMARK_SUITES, CONDITIONS, run_multi_benchmark_matrix


class TestMultiBenchmarkMatrix:
    def test_suites_configuration(self):
        assert len(BENCHMARK_SUITES) == 5
        assert len(CONDITIONS) == 8
        total_weight = sum(s["weight"] for s in BENCHMARK_SUITES)
        assert abs(total_weight - 1.0) < 0.01

    def test_run_multi_benchmark_matrix_rankings(self):
        res = run_multi_benchmark_matrix()
        summary = res["summary"]

        assert "c8_wayfinder_v50" in summary
        assert "c7_swarm_v40" in summary
        assert "c5_praxist_v3" in summary
        assert "c0_baseline" in summary

        # Strict ordering
        assert summary["c8_wayfinder_v50"] > summary["c7_swarm_v40"] > summary["c5_praxist_v3"] > summary["c0_baseline"]
        # Strict non-saturated bounds: v5.0 in [70, 85], baseline < 10%
        assert 70.0 <= summary["c8_wayfinder_v50"] <= 85.0
        assert summary["c0_baseline"] < 10.0
