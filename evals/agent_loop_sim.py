#!/usr/bin/env python3
"""Multi-Turn AutoEvolve Loop Simulator.

Demonstrates how the interactive execution loop (make diff -> grade -> keep or revert -> retry with trace)
solves complex tasks (like security and error handling) where single-turn prompt generation fails.

Usage:
    python evals/agent_loop_sim.py --scenario 05_security --model llama-3.3-70b-versatile
    python evals/agent_loop_sim.py --all
"""
from __future__ import annotations

import argparse
import os
import sys
import json
import urllib.request

# Ensure evals modules can be imported
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from profile import TASKS, code_file, extract_code, grade_code, read_text, call_groq


def run_loop_simulation(
    scenario: str,
    model: str = "llama-3.3-70b-versatile",
    max_turns: int = 3,
    api_key: str | None = None,
) -> dict:
    """Run an interactive keep-or-revert loop simulation for a scenario."""
    filename = code_file(scenario)
    starter = read_text(os.path.join("evals", "scenarios", scenario, filename))
    task_desc = TASKS[scenario]

    best_code = starter
    best_score = 0
    best_checks = []

    # Initial baseline check on starter
    graded_init, err_init = grade_code(scenario, starter, sandboxed=False)
    if graded_init:
        best_score = sum(1 for _, ok in graded_init if ok)
        best_checks = graded_init

    history = []
    print(f"\n[loop_sim] Starting multi-turn loop for scenario: {scenario} (Baseline: {best_score} checks passed)")

    current_code = starter

    for turn in range(1, max_turns + 1):
        if turn == 1:
            prompt = (
                f"Task: {task_desc}\n\n"
                f"File `{filename}`:\n```python\n{current_code}\n```\n\n"
                "Return ONLY the complete corrected contents of the file in a single fenced code block."
            )
        else:
            failed_msgs = [f"- {name} (failed)" for name, ok in best_checks if not ok]
            prompt = (
                f"Previous attempt on `{filename}` passed {best_score}/{len(best_checks)} checks.\n"
                f"Failing checks:\n" + "\n".join(failed_msgs) + "\n\n"
                f"Current best code for `{filename}`:\n```python\n{best_code}\n```\n\n"
                "Fix the remaining failure cases while keeping existing passing checks working. "
                "Return ONLY the complete updated file in a fenced code block."
            )

        messages = [
            {"role": "system", "content": "You are a disciplined coding agent following the AutoEvolve keep-or-revert loop."},
            {"role": "user", "content": prompt},
        ]

        content, tokens, error = call_groq(model, messages, temperature=0.2, api_key=api_key)
        if error or not content:
            print(f"  Turn {turn}: API Error [{error}]")
            break

        proposed_code = extract_code(content)
        graded, grade_err = grade_code(scenario, proposed_code, sandboxed=False)

        if grade_err or graded is None:
            print(f"  Turn {turn}: REVERTED (Grader error: {grade_err or 'syntax crash'})")
            history.append({"turn": turn, "action": "revert", "score": best_score, "reason": "grader_error"})
            continue

        score = sum(1 for _, ok in graded if ok)
        total = len(graded)

        if score > best_score:
            print(f"  Turn {turn}: KEEP! Improved score from {best_score}/{total} to {score}/{total}")
            best_code = proposed_code
            best_score = score
            best_checks = graded
            history.append({"turn": turn, "action": "keep", "score": score, "total": total})
            if score == total:
                print(f"  [SUCCESS] All {total} checks passed on Turn {turn}!")
                return {"scenario": scenario, "outcome": "pass", "turns": turn, "final_score": score, "total": total, "history": history}
        else:
            print(f"  Turn {turn}: REVERTED (Hypothesis score {score}/{total} <= baseline {best_score}/{total})")
            history.append({"turn": turn, "action": "revert", "score": score, "total": total})

    outcome = "pass" if (best_checks and all(ok for _, ok in best_checks)) else "fail"
    return {"scenario": scenario, "outcome": outcome, "turns": len(history), "final_score": best_score, "total": len(best_checks) if best_checks else 0, "history": history}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", help="Scenario ID (e.g. 05_security)")
    ap.add_argument("--all", action="store_true", help="Run loop simulation across all scenarios")
    ap.add_argument("--model", default="llama-3.3-70b-versatile")
    ap.add_argument("--turns", type=int, default=3)
    ap.add_argument("--api-key", help="Groq API Key override")
    args = ap.parse_args()

    scenarios = sorted(TASKS) if args.all else ([args.scenario] if args.scenario else ["05_security"])
    results = []

    for sc in scenarios:
        if sc not in TASKS:
            print(f"Unknown scenario: {sc}", file=sys.stderr)
            continue
        res = run_loop_simulation(sc, model=args.model, max_turns=args.turns, api_key=args.api_key)
        results.append(res)

    print("\n" + "=" * 60)
    print("MULTI-TURN AUTOEVOLVE SIMULATION SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  {r['scenario']:16} {r['outcome'].upper():6} ({r['final_score']}/{r['total']} checks, {r['turns']} turns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
