#!/usr/bin/env python3
"""Run an AutoEvolve eval scenario and score it.

Each scenario in `evals/scenarios/<name>/` ships broken starter code plus a grader
(`grade.py`) kept separate from the code under test, so the ruler stays out of the thing it
measures. The starter FAILS on purpose: that gap is what the mindset should close.

Usage:
    python3 evals/run.py                 # list scenarios
    python3 evals/run.py 01_bugfix       # grade one scenario (exit 1 if it fails)
    python3 evals/run.py --all           # grade every scenario
    python3 evals/run.py --smoke         # verify the harness runs (exit 1 only on a grader error)

Point your agent (with AutoEvolve loaded) at a scenario's code, let it work, then re-run
this to watch the score move from FAIL to PASS. No dependencies, standard library only.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.join(ROOT, "scenarios")


def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scenarios() -> list[str]:
    return sorted(
        d for d in os.listdir(SCENARIOS)
        if os.path.isdir(os.path.join(SCENARIOS, d)) and not d.startswith(".")
    )


def grade(name: str) -> str:
    """Return 'pass', 'fail', or 'error' and print the per-check results."""
    d = os.path.join(SCENARIOS, name)
    print(f"\n== {name} ==")
    try:
        grader = _load(os.path.join(d, "grade.py"), f"{name}_grade")
        results = grader.checks()
    except Exception:
        print("  [ERROR] the grader itself failed to run (this is a harness bug):")
        print("    " + traceback.format_exc().replace("\n", "\n    ").rstrip())
        return "error"
    ok_all = True
    for cname, ok, detail in results:
        ok_all = ok_all and ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {cname}" + (f"  ({detail})" if detail else ""))
    print(f"  overall: {'PASS' if ok_all else 'FAIL'}")
    return "pass" if ok_all else "fail"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("scenarios:", ", ".join(scenarios()))
        print("run: python3 evals/run.py <scenario> | --all | --smoke")
        return 0

    smoke = args[0] == "--smoke"
    names = scenarios() if args[0] in ("--all", "--smoke") else args
    statuses = [grade(n) for n in names]

    if smoke:
        # Smoke only cares that the harness executes; scenarios FAIL by design until solved.
        errored = statuses.count("error")
        print(f"\nsmoke: {len(statuses)} scenario(s) ran, {errored} harness error(s).")
        return 1 if errored else 0
    return 0 if all(s == "pass" for s in statuses) else 1


if __name__ == "__main__":
    sys.exit(main())
