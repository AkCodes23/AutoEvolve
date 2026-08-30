#!/usr/bin/env python3
"""Empirical Code Quality & Implementation Efficiency Benchmark Runner.

Measures actual output-side software engineering metrics across real codebase scenarios:
1. Functional Pass Rate (%) — Hard gate correctness
2. Caller Contract Preservation (%) — Zero broken downstream dependencies
3. AST Brevity & YAGNI Score (%) — Elimination of over-engineered boilerplate
4. Comment Cleanliness & Hygiene (%) — Zero dead code / narration noise
5. Test Integrity Rate (%) — Zero goalpost tampering
6. Worktree Reversibility (%) — Zero untracked dirty residue
7. Implementation Execution Efficiency — Real execution latency (seconds)
8. Multi-Scenario Failure Mode Resistance — Security, resilience, concurrency, memory
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from typing import Any, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.runner import BenchmarkRunner


@dataclasses.dataclass
class CodeQualityMetrics:
    condition_name: str
    functional_pass_rate: float
    caller_safety_rate: float
    yagni_brevity_score: float
    comment_hygiene_score: float
    test_integrity_rate: float
    tree_cleanliness_rate: float
    avg_execution_latency_s: float
    composite_code_quality_index: float
    scenario_details: Dict[str, Any]


def run_code_quality_benchmark(repo_root: str = REPO_ROOT) -> Dict[str, Any]:
    """Execute matrix of real codebase scenarios and measure output code quality."""
    matrix_summary_path = os.path.join(repo_root, "benchmarks", "results", "matrix_summary.json")

    # If matrix summary doesn't exist, run it
    if not os.path.exists(matrix_summary_path):
        from benchmarks.run_benchmark import run_full_matrix
        run_full_matrix(repo_root)

    with open(matrix_summary_path, "r", encoding="utf-8") as f:
        matrix_data = json.load(f)

    conditions_raw = matrix_data.get("conditions", {})
    output_report: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "conditions": {},
        "comparison_table": {},
        "extended_evaluations": {},
    }

    print("\n" + "=" * 95)
    print("  EMPIRICAL OUTPUT CODE QUALITY & IMPLEMENTATION EFFICIENCY BENCHMARK")
    print("=" * 95)
    print(
        f"{'Condition':30} | {'Pass Rate':>9} | {'Caller Safe':>11} | {'Brevity':>8} | {'Hygiene':>8} | {'Latency':>8} | {'Quality Index':>13}"
    )
    print("-" * 95)

    for cond_id, cond_info in conditions_raw.items():
        results = cond_info.get("results", [])
        total_sc = len(results)
        if total_sc == 0:
            continue

        passed_count = sum(1 for r in results if r["details"].get("test_passed", False))
        pass_rate = round((passed_count / total_sc) * 100.0, 1)

        # 1. Caller Safety Rate (Scenario 1 & multi-caller)
        s1_res = next((r for r in results if r["scenario_id"] == "s1_blast_radius"), None)
        caller_safety = (
            s1_res["details"].get("blast_radius", {}).get("blast_radius_score", 1.0) * 100.0
            if s1_res
            else 100.0
        )

        # 2. YAGNI Brevity (Scenario 3)
        s3_res = next((r for r in results if r["scenario_id"] == "s3_yagni_minimalism"), None)
        brevity = (
            s3_res["details"].get("yagni", {}).get("brevity_score", 1.0) * 100.0
            if s3_res
            else 100.0
        )

        # 3. Comment Hygiene (Scenario 6)
        s6_res = next((r for r in results if r["scenario_id"] == "s6_anti_comment"), None)
        hygiene = (
            s6_res["details"].get("comment_audit", {}).get("comment_score", 1.0) * 100.0
            if s6_res
            else 100.0
        )

        # 4. Test Integrity (Scenario 2)
        s2_res = next((r for r in results if r["scenario_id"] == "s2_goalpost_tampering"), None)
        integrity = (
            s2_res["details"].get("hash_guard", {}).get("integrity_score", 1.0) * 100.0
            if s2_res
            else 100.0
        )

        # 5. Tree Cleanliness (Scenario 5)
        s5_res = next((r for r in results if r["scenario_id"] == "s5_speculative_rollback"), None)
        cleanliness = (
            s5_res["details"].get("git_audit", {}).get("reversibility_score", 1.0) * 100.0
            if s5_res
            else 100.0
        )

        # 6. Average Execution Latency
        avg_latency = sum(r.get("duration_seconds", 0.0) for r in results) / total_sc
        composite_score = cond_info.get("composite_score", 0.0)

        quality_entry = {
            "condition_id": cond_id,
            "name": cond_info.get("name", cond_id),
            "functional_pass_rate_pct": pass_rate,
            "caller_safety_rate_pct": round(caller_safety, 1),
            "yagni_brevity_score_pct": round(brevity, 1),
            "comment_hygiene_score_pct": round(hygiene, 1),
            "test_integrity_rate_pct": round(integrity, 1),
            "tree_cleanliness_rate_pct": round(cleanliness, 1),
            "avg_execution_latency_s": round(avg_latency, 3),
            "composite_code_quality_index": composite_score,
        }

        output_report["conditions"][cond_id] = quality_entry

        print(
            f"{cond_info['name'][:30]:30} | {pass_rate:8.1f}% | {caller_safety:10.1f}% | {brevity:7.1f}% | {hygiene:7.1f}% | {avg_latency:7.3f}s | {composite_score:12.1f}%"
        )

    print("=" * 95)

    # Extended Scenario Corpus Evaluation
    print("\n>>> Executing Extended Scenario Suite Verification (S7 .. S32)...")
    runner = BenchmarkRunner(repo_root=repo_root)
    all_scenarios = runner.list_scenarios()

    extended_results = []
    for sc in all_scenarios:
        sc_id = sc["id"]
        # Skip core 6 which were evaluated in matrix
        if sc_id in [
            "s1_blast_radius",
            "s2_goalpost_tampering",
            "s3_yagni_minimalism",
            "s4_context_frugality",
            "s5_speculative_rollback",
            "s6_anti_comment",
        ]:
            continue

        res = runner.evaluate_scenario(sc_id)
        extended_results.append({
            "id": sc_id,
            "name": sc.get("name", sc_id),
            "category": sc.get("category", "general"),
            "passed": res.passed,
            "score": res.score,
            "duration_s": res.duration_seconds,
        })

    ext_passed = sum(1 for r in extended_results if r["passed"])
    ext_total = len(extended_results)
    ext_pass_rate = round((ext_passed / ext_total) * 100.0, 1) if ext_total > 0 else 100.0

    output_report["extended_evaluations"] = {
        "total_scenarios": ext_total,
        "passed_scenarios": ext_passed,
        "pass_rate_pct": ext_pass_rate,
        "scenarios": extended_results,
    }

    print(f"  Extended Corpus: {ext_passed}/{ext_total} scenarios passed ({ext_pass_rate}%)")
    print("=" * 95)

    out_file = os.path.join(repo_root, "benchmarks", "results", "code_quality_benchmark_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_report, f, indent=2)

    print(f"\nSaved empirical code quality benchmark report to: {out_file}\n")
    return output_report


if __name__ == "__main__":
    run_code_quality_benchmark()
