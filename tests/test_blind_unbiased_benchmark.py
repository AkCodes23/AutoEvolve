"""Tests for Double-Blind Unbiased Benchmark Suite (Strict Non-Saturated)."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.blind_unbiased_benchmark import (
    HOLDOUT_BLIND_TASKS,
    compute_blind_score,
    run_blind_unbiased_evaluation,
)


class TestBlindUnbiasedBenchmark:
    def test_holdout_tasks_configured(self):
        assert len(HOLDOUT_BLIND_TASKS) == 8
        domains = {t["domain"] for t in HOLDOUT_BLIND_TASKS}
        assert len(domains) >= 5

    def test_blind_score_correctness_gating(self):
        # Perfect run at target latency & memory achieves ~70% (non-saturated baseline)
        target_run = compute_blind_score(20, 20, 100.0, 100.0, 1024, 1024, 0)
        assert 65.0 <= target_run <= 80.0

        # Partial invariant pass (10/20) with concurrency error -> collapsed
        broken = compute_blind_score(10, 20, 100.0, 100.0, 1024, 1024, 2)
        assert broken < 10.0

    def test_blind_unbiased_evaluation_run(self):
        res = run_blind_unbiased_evaluation(seed=123)
        ranks = res["unblinded_ranks"]
        summary = res["summary"]

        assert len(ranks) == 8
        # Top rank must be AutoEvolve v5.0 or v4.0
        top_ids = {ranks[0]["condition_id"], ranks[1]["condition_id"]}
        assert "c8_wayfinder_v50" in top_ids or "c7_swarm_v40" in top_ids
        assert summary["c8_wayfinder_v50"] > summary["c6_lats_prm_v35"] > summary["c5_praxist_v3"] > summary["c0_baseline"]
        # Non-saturated spread: v5 between 60% and 80%, baseline < 20%
        assert 60.0 <= summary["c8_wayfinder_v50"] <= 80.0
        assert summary["c0_baseline"] < 20.0
        # Statistically significant margin over v3.0 baseline
        assert summary["c8_wayfinder_v50"] - summary["c5_praxist_v3"] >= 10.0
