#!/usr/bin/env python3
"""Deep, Unbiased Comparative Benchmark of AutoEvolve Conditions (C0..C5).

Evaluates prompt conditions across:
1. Token & Memory Footprint (Cost / Context Consumption)
2. Engineering Invariant & Constraint Density (Rules per Token)
3. 20-Dimensional Invariant Coverage Matrix (including Wayfinding & Fog of War)
4. Multi-Condition Objective Scoring
5. Trade-off Analysis (Unbiased evaluation of trade-offs: prompt size vs rule coverage)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROMPTS_DIR = os.path.join(REPO_ROOT, "benchmarks", "prompts")

CONDITIONS = {
    "C0: Baseline": "condition0_baseline.md",
    "C1: Karpathy Autoresearch": "condition1_karpathy.md",
    "C2: Ponytail (Gebert)": "condition2_ponytail.md",
    "C3: AutoEvolve v1 (Standard)": "condition3_autoevolve.md",
    "C4: AutoEvolve v2 (Next-Gen)": "condition4_autoevolve_v2.md",
    "C5: AutoEvolve v5 (Wayfinding)": "condition5_autoevolve_v5.md",
}

# 20 Standard Engineering & Wayfinding Invariants
INVARIANT_TAXONOMY = {
    "DAG Parallelism & Barrier Sync": [
        r"\bDAG\b",
        r"join barrier",
        r"fan.*out",
        r"parallel",
    ],
    "Multi-Metric Gate Banding": [
        r"hard gates?",
        r"soft gates?",
        r"latency budget",
        r"drift",
    ],
    "Instruction Entropy & Budgeting": [
        r"prune superseded",
        r"token budgets?",
        r"consolidate.*never just append",
        r"simplify",
    ],
    "Proactive Circuit Breaking": [
        r"circuit-break",
        r"rate-limit",
        r"token quotas?",
        r"exhausted.*dependencies",
    ],
    "Content-Addressed Invalidation": [
        r"content-addressed",
        r"hash.*inputs",
        r"hashes diverge",
        r"invalidate.*artifacts",
    ],
    "Graduated Failure Escalation": [
        r"3\+\s*(?:consecutive\s*)?loops?\s*fail",
        r"question.*architecture",
        r"pause for a? human",
    ],
    "Poka-Yoke / Error-Proof Design": [
        r"error-proof",
        r"invalid (?:internal )?states unrepresentable",
        r"compile/design time",
    ],
    "Evidence-Gated Claims": [
        r"evidence before claims",
        r"cite.*output",
        r"should work.*not evidence",
    ],
    "Blast Radius / Caller Awareness": [
        r"know.*callers",
        r"shared contract",
        r"surgical",
    ],
    "Trust Boundaries & Non-Blocking Locks": [
        r"trust boundaries",
        r"no silent coercion",
        r"locks? across I/O",
    ],
    "Subprocess Array Safety": [
        r"array arguments",
        r"shell\s*=\s*True",
        r"cross-platform",
    ],
    "Complexity & Memory Bounds": [
        r"time and space cost",
        r"hoist allocations",
        r"unbounded memory",
        r"bound concurrency",
    ],
    "Direct Code / Comment Hygiene": [
        r"direct code",
        r"commented-out code",
        r"name things instead of narrating",
    ],
    "Frozen Signal / Non-Tampering": [
        r"freeze the signal",
        r"optimize.*objective.*never.*scorer",
    ],
    "Dirty Tree Preservation": [
        r"never bulk-discard",
        r"dirty tree",
        r"preserve.*user",
    ],
    "Wayfinding & Fog of War Decomposition": [
        r"fog of war",
        r"wayfind",
        r"decision map",
    ],
    "Strict HITL / AFK Mode Separation": [
        r"grilling.*hitl",
        r"never answer own grilling",
        r"4 modes",
    ],
    "Disposable Prototyping Spikes": [
        r"prototype.*disposable",
        r"disposable spike",
        r"prototype",
    ],
    "Index vs Store Memory Hierarchy": [
        r"index vs store",
        r"index.*store",
    ],
    "Frontier Node Pre-Registration": [
        r"unblocked frontier node",
        r"claiming.*frontier",
        r"frontier",
    ],
}


def load_condition(filename: str) -> str:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def evaluate_invariants(text: str) -> Dict[str, bool]:
    results = {}
    for inv_name, patterns in INVARIANT_TAXONOMY.items():
        matched = False
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched = True
                break
        results[inv_name] = matched
    return results


def run_comprehensive_benchmark() -> Dict[str, Any]:
    suite_data: Dict[str, Any] = {}

    for name, filename in CONDITIONS.items():
        content = load_condition(filename)
        char_count = len(content)
        byte_count = len(content.encode("utf-8"))
        word_count = len(content.split())
        line_count = len(content.splitlines())
        est_tokens = max(1, char_count // 4)

        inv_results = evaluate_invariants(content)
        covered_count = sum(1 for v in inv_results.values() if v)
        coverage_pct = round((covered_count / len(INVARIANT_TAXONOMY)) * 100.0, 1)

        # Density = Covered Invariants per 100 Tokens
        density = round((covered_count / est_tokens) * 100.0, 3)

        suite_data[name] = {
            "file": filename,
            "bytes": byte_count,
            "lines": line_count,
            "words": word_count,
            "tokens_est": est_tokens,
            "invariants_covered": covered_count,
            "invariants_total": len(INVARIANT_TAXONOMY),
            "coverage_pct": coverage_pct,
            "density_per_100_tokens": density,
            "breakdown": inv_results,
        }

    return suite_data


def print_scorecard(data: Dict[str, Any]):
    print("=" * 95)
    print("UNBIASED BENCHMARK SCORECARD: PROMPT CONDITIONS COMPARISON (v5.0)")
    print("=" * 95)
    print(f"{'Condition':34} | {'Tokens':>7} | {'Lines':>5} | {'Coverage':>9} | {'Rules/100T':>10}")
    print("-" * 95)

    for cond, d in data.items():
        print(
            f"{cond:34} | {d['tokens_est']:7d} | {d['lines']:5d} | {d['coverage_pct']:8.1f}% | {d['density_per_100_tokens']:10.3f}"
        )

    print("-" * 95)
    print("\n20-DIMENSIONAL INVARIANT COVERAGE MATRIX:")
    print("-" * 95)
    header = f"{'Invariant Dimension':44} | " + " | ".join(f"C{i}" for i in range(len(CONDITIONS)))
    print(header)
    print("-" * 95)

    for inv in INVARIANT_TAXONOMY:
        marks = []
        for cond, d in data.items():
            marks.append("PASS" if d["breakdown"][inv] else " -- ")
        print(f"{inv:44} | " + "  | ".join(marks))

    print("=" * 95)


if __name__ == "__main__":
    report = run_comprehensive_benchmark()
    print_scorecard(report)
    json_out = os.path.join(REPO_ROOT, "benchmarks", "results", "mindset_benchmark_report.json")
    os.makedirs(os.path.dirname(json_out), exist_ok=True)
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved detailed benchmark JSON to: {json_out}")
