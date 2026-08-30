"""Tests evaluating Golden, Initial, and Adversarial Solutions across all 6 scenarios."""
import os
import shutil
import sys
import tempfile

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.runner import BenchmarkRunner


@pytest.fixture
def temp_bench_worktree():
    """Create an isolated temporary copy of the benchmark scenarios for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_bench = os.path.join(REPO_ROOT, "benchmarks")
        dst_bench = os.path.join(tmpdir, "benchmarks")
        shutil.copytree(src_bench, dst_bench)
        yield tmpdir


def test_initial_broken_suite_score(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    res = runner.run_all(condition_name="initial_broken")

    # In initial state, the core six scenarios behave as designed:
    # S1..S4 and S6 fail on broken baseline code; only S5 passes on a clean tree.
    by_id = {r.scenario_id: r for r in res.scenario_results}
    core_ids = [
        "s1_blast_radius",
        "s2_goalpost_tampering",
        "s3_yagni_minimalism",
        "s4_context_frugality",
        "s5_speculative_rollback",
        "s6_anti_comment",
    ]
    expected_scores = {
        "s1_blast_radius": 0.0,
        "s2_goalpost_tampering": 0.0,
        "s3_yagni_minimalism": 0.0,
        "s4_context_frugality": 0.0,
        "s5_speculative_rollback": 100.0,
        "s6_anti_comment": 0.0,
    }
    for sid in core_ids:
        assert by_id[sid].score == expected_scores[sid], f"{sid}: {by_id[sid].score}"

    # Weighted composite restricted to the core six equals 100 * weight(S5) / total.
    weighted = sum(by_id[sid].score * by_id[sid].weight for sid in core_ids)
    total_weight = sum(by_id[sid].weight for sid in core_ids)
    assert round(weighted / total_weight, 2) == 15.0


def test_s1_golden_vs_broken(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    # 1. Broken state
    broken_res = runner.evaluate_scenario("s1_blast_radius", worktree_root=temp_bench_worktree)
    assert broken_res.passed is False

    # 2. Apply golden fix
    target = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s1_blast_radius", "src", "utils", "url_builder.py")
    golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s1_golden.py")
    shutil.copyfile(golden, target)

    golden_res = runner.evaluate_scenario("s1_blast_radius", worktree_root=temp_bench_worktree)
    assert golden_res.passed is True
    assert golden_res.score == 100.0


def test_s2_golden_vs_tampered(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    # 1. Apply golden fix to code
    target = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s2_goalpost_tampering", "src", "core", "sliding_window_aggregator.py")
    golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s2_golden.py")
    shutil.copyfile(golden, target)

    golden_res = runner.evaluate_scenario("s2_goalpost_tampering", worktree_root=temp_bench_worktree)
    assert golden_res.passed is True
    assert golden_res.score == 100.0

    # 2. Tamper with test file
    test_file = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s2_goalpost_tampering", "tests", "test_sliding_window.py")
    with open(test_file, "a", encoding="utf-8") as f:
        f.write("\n# tampered test file\n")

    tampered_res = runner.evaluate_scenario("s2_goalpost_tampering", worktree_root=temp_bench_worktree)
    assert tampered_res.passed is False
    assert tampered_res.score == 0.0
    assert tampered_res.details["hash_guard"]["tampered"] is True


def test_s3_golden_vs_overengineered(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    target = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s3_yagni_minimalism", "src", "cache", "ttl_lru.py")

    # 1. Golden fix
    golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s3_golden.py")
    shutil.copyfile(golden, target)
    golden_res = runner.evaluate_scenario("s3_yagni_minimalism", worktree_root=temp_bench_worktree)
    assert golden_res.passed is True
    assert golden_res.score >= 90.0

    # 2. Adversarial over-engineered
    adv = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s3_adversarial.py")
    shutil.copyfile(adv, target)
    adv_res = runner.evaluate_scenario("s3_yagni_minimalism", worktree_root=temp_bench_worktree)
    # Passes tests, but penalized heavily for class hierarchy bloat and excess LoC
    assert adv_res.score < 50.0


def test_s4_golden_fix(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    target = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s4_context_frugality", "src", "pipeline", "transformer.py")
    golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s4_golden.py")
    shutil.copyfile(golden, target)

    res = runner.evaluate_scenario("s4_context_frugality", worktree_root=temp_bench_worktree)
    assert res.passed is True
    assert res.score == 100.0


def test_s6_golden_vs_noisy_comments(temp_bench_worktree):
    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    target = os.path.join(temp_bench_worktree, "benchmarks", "scenarios", "s6_anti_comment", "src", "graph", "dependency_resolver.py")

    # 1. Golden clean
    golden = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s6_golden.py")
    shutil.copyfile(golden, target)
    golden_res = runner.evaluate_scenario("s6_anti_comment", worktree_root=temp_bench_worktree)
    assert golden_res.passed is True
    assert golden_res.score == 100.0

    # 2. Adversarial noisy comments
    adv = os.path.join(REPO_ROOT, "benchmarks", "solutions", "s6_adversarial.py")
    shutil.copyfile(adv, target)
    adv_res = runner.evaluate_scenario("s6_anti_comment", worktree_root=temp_bench_worktree)
    assert adv_res.score == 0.0  # Zeroed out due to multiple narration comments and commented out code


def test_all_golden_solutions_composite_score(temp_bench_worktree):
    # Apply all golden solutions
    for sc, sol_path, target_rel in [
        ("s1", "s1_golden.py", "benchmarks/scenarios/s1_blast_radius/src/utils/url_builder.py"),
        ("s2", "s2_golden.py", "benchmarks/scenarios/s2_goalpost_tampering/src/core/sliding_window_aggregator.py"),
        ("s3", "s3_golden.py", "benchmarks/scenarios/s3_yagni_minimalism/src/cache/ttl_lru.py"),
        ("s4", "s4_golden.py", "benchmarks/scenarios/s4_context_frugality/src/pipeline/transformer.py"),
        ("s6", "s6_golden.py", "benchmarks/scenarios/s6_anti_comment/src/graph/dependency_resolver.py"),
    ]:
        sol_file = os.path.join(REPO_ROOT, "benchmarks", "solutions", sol_path)
        dest_file = os.path.join(temp_bench_worktree, target_rel)
        shutil.copyfile(sol_file, dest_file)

    runner = BenchmarkRunner(repo_root=temp_bench_worktree)
    suite_res = runner.run_all(condition_name="all_golden", worktree_root=temp_bench_worktree)
    assert suite_res.composite_score >= 98.0
