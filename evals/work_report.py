#!/usr/bin/env python3
"""Compare conditions on WORK DONE rather than on tokens spent.

    python3 evals/work_report.py evals/results/*.jsonl
    python3 evals/work_report.py --model llama-3.1-8b-instant evals/results/*.jsonl

Tokens are an input price. Checks passed are an output score. Neither says anything about how much
of the file a change disturbed, which is the only thing this project actually claims: smallest
correct diff, deletion over addition, do not break what already worked. Those are claims about
work, and `evals/profile.py` records the raw numbers on every trial (`churn`, `lines_added`,
`lines_removed`, `starter_lines_kept`), computed from the produced source with no model calls.

The headline column is gain per 10 lines of churn: graded checks gained ABOVE THE STARTER, divided
by the lines the submission disturbed to gain them. Credit goes only to the improvement, because
the starters already pass some checks for free, so scoring the raw total would rank a submission
that changed nothing as maximally efficient.

Restrict to one model with --model unless every model completed every cell. A mean pooled across
models is not a comparison: a condition whose rows happen to come from the weakest model looks
worse than one that drew the strongest, and nothing in the mean corrects for it.

Standard library only. No network, no key, no Docker.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import random
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN = os.path.join(ROOT, "evals", "scenarios")
ORDER = ["control", "karpathy", "ponytail", "core", "core_v2", "full"]
# A bootstrap over a handful of blocks excludes zero on noise alone. This project has already had
# three "effects" reverse on replication, so the label refuses to claim significance below this.
MIN_BLOCKS = 5


def starter_source(scenario: str) -> str:
    directory = os.path.join(SCEN, scenario)
    for name in sorted(os.listdir(directory)):
        if name.endswith(".py") and name != "grade.py":
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                return handle.read()
    raise FileNotFoundError(f"no code-under-test file in {scenario}")


def starter_score(scenario: str, cache: dict = {}) -> float:
    """Fraction of checks the untouched starter already passes."""
    if scenario in cache:
        return cache[scenario]
    spec = importlib.util.spec_from_file_location(
        f"_sb_{scenario}", os.path.join(SCEN, scenario, "grade.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = module.checks()
    cache[scenario] = sum(1 for _, ok, _ in results if ok) / len(results)
    return cache[scenario]


def boot(values: list[float], reps: int = 20000, seed: int = 20260727) -> tuple[float, float]:
    if len(values) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("results", nargs="+", help="JSON Lines files written by profile.py")
    parser.add_argument("--model", help="restrict to one model, for a balanced comparison")
    args = parser.parse_args()

    rows = []
    for pattern in args.results:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as handle:
                    rows += [json.loads(line) for line in handle if line.strip()]
    if args.model:
        rows = [r for r in rows if r.get("model") == args.model]
    usable = [r for r in rows if r.get("churn") is not None and r.get("checks_total")]
    if not usable:
        print("No rows carry the work axis. Run `profile.py --regrade <file>` to backfill it "
              "onto a dataset that stored the graded source.")
        return 1

    models = sorted({r["model"] for r in usable})
    if len(models) > 1 and not args.model:
        print(f"WARNING: {len(models)} models pooled. Pass --model for a balanced comparison; a "
              "condition that drew a stronger model will look better for that reason alone.\n")

    per: dict = defaultdict(lambda: defaultdict(list))
    blocks: dict = defaultdict(lambda: defaultdict(list))
    for r in usable:
        gained = max(r["checks_passed"] / r["checks_total"] - starter_score(r["scenario"]), 0.0)
        cond = r["condition"]
        per[cond]["churn"].append(r["churn"])
        per[cond]["removed"].append(r["lines_removed"])
        per[cond]["kept"].append(r.get("starter_lines_kept") or 0.0)
        per[cond]["gained"].append(gained)
        per[cond]["efficiency"].append(gained / max(r["churn"], 1) * 10)
        blocks[cond][(r["model"], r["scenario"])].append(r["churn"])

    conds = [c for c in ORDER if c in per] + sorted(set(per) - set(ORDER))
    label = args.model or f"{len(models)} models pooled"
    print(f"WORK DONE ({label}, {len(usable)} trials)\n")
    print(f"{'condition':10} {'churn':>7} {'removed':>8} {'kept':>7} {'gained':>8} {'gain/10 lines':>14}")
    for cond in conds:
        d = per[cond]
        n = len(d["churn"])
        print(f"{cond:10} {sum(d['churn']) / n:7.1f} {sum(d['removed']) / n:8.1f} "
              f"{100 * sum(d['kept']) / n:6.0f}% {100 * sum(d['gained']) / n:7.1f}% "
              f"{sum(d['efficiency']) / n:14.2f}")

    base = "control" if "control" in per else conds[0]
    print(f"\nChurn vs {base}, blocked on (model, scenario). Negative is the stated goal:")
    for cond in conds:
        if cond == base:
            continue
        shared = sorted(set(blocks[base]) & set(blocks[cond]))
        if not shared:
            continue
        diffs = [sum(blocks[cond][k]) / len(blocks[cond][k])
                 - sum(blocks[base][k]) / len(blocks[base][k]) for k in shared]
        lo, hi = boot(diffs)
        mean = sum(diffs) / len(diffs)
        if len(shared) < MIN_BLOCKS:
            verdict = f"UNDERPOWERED ({len(shared)} blocks)"
        elif lo > 0 or hi < 0:
            verdict = "excludes zero"
        else:
            verdict = "not significant"
        print(f"  {cond:10} {mean:+7.1f} lines  95% CI [{lo:+.1f}, {hi:+.1f}]  "
              f"blocks={len(shared)}  {verdict}")

    print("\nTwo conditions at the same score are not equal engineering if one changed three lines")
    print("and the other rewrote the file. That is what this table is for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
