"""Tests for AutoEvolve v3.5: Tree Search (LATS) and PRM Step Critic."""
from __future__ import annotations

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.tree_search import ProcessRewardModel, LATSNode
from scripts.fuzz_invariants import check_idempotence, check_scale_linearity


class TestV35TreeSearchAndPRM:
    def test_prm_step_critic_clean_diff(self):
        diff = "+ def optimize_buffer():\n+     return True"
        res = ProcessRewardModel.evaluate_step(diff, "core", "Optimize buffer")
        assert res["step_score"] >= 0.8
        assert res["status"] == "APPROVED"
        assert len(res["reasons"]) == 0

    def test_prm_step_critic_anti_goal_rejection(self):
        diff = "+ import threading\n+ global_lock = threading.Lock()"
        res = ProcessRewardModel.evaluate_step(diff, "core", "Optimize", anti_goals=["global_lock"])
        assert res["step_score"] < 0.5
        assert res["status"] == "REJECTED"
        assert any("Anti-goal violation" in r for r in res["reasons"])

    def test_prm_step_critic_tautology_rejection(self):
        diff = "+ def test_something():\n+     assert True"
        res = ProcessRewardModel.evaluate_step(diff, "tests", "Add tests")
        assert res["step_score"] == 0.0
        assert res["status"] == "REJECTED"

    def test_lats_node_branching_and_uct(self):
        root = LATSNode("root", "Baseline", "root")
        child_simd = LATSNode("simd", "Vectorize", "simd", parent=root)
        child_lockfree = LATSNode("lockfree", "CAS ring", "concurrency", parent=root)
        root.children.extend([child_simd, child_lockfree])

        assert child_simd.uct_score(0) == float("inf")

        child_simd.backpropagate(0.85)
        assert child_simd.visits == 1
        assert child_simd.value == 0.85
        assert root.visits == 1
        assert root.value == 0.85

        child_lockfree.backpropagate(0.40)
        assert root.visits == 2

        assert child_simd.value > child_lockfree.value

    def test_metamorphic_idempotence(self):
        def idemp_fn(x):
            return abs(x)

        res = check_idempotence(idemp_fn, [-5, -2, 0, 3, 7])
        assert res["rate"] == 1.0

    def test_metamorphic_scale_linearity(self):
        def linear_fn(arr):
            return sum(x * 2 for x in arr)

        res = check_scale_linearity(linear_fn, base_size=500, scale_factor=5)
        assert res["is_subquadratic"] is True
