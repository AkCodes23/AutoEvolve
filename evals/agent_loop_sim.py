#!/usr/bin/env python3
"""Multi-Turn AutoEvolve Loop Simulator.

Runs several attempts at one scenario, grading each and carrying the best code forward.

READ THIS BEFORE CITING ANY NUMBER FROM THIS TOOL. It is best-of-N sampling with a graded
oracle, not the keep-or-revert loop AGENTS.md describes, and the two are not the same claim:

  - `best_score` only ever moves upward, so `final_score >= turn_1_score` holds by construction.
    This runner structurally cannot report a regression, which is the thing keep-or-revert exists
    to prevent. A rising number here is not evidence the loop protects a codebase.
  - It sees the grader's verdict between turns. A real agent does not have the frozen scorer's
    per-check output handed to it, so any advantage measured here is partly oracle access.
    The prompt no longer leaks the failing check NAMES (that alone was worth several points),
    but the pass count is still oracle information.

For the honest prompt-condition comparison use evals/profile.py, which is blind and randomized.
Use this tool to observe multi-turn behavior qualitatively, and report `turn_1_score` alongside
`final_score` so a reader can see what the extra turns actually bought.

Usage:
    python evals/agent_loop_sim.py --scenario 05_security --model llama-3.3-70b-versatile
    python evals/agent_loop_sim.py --all --output results/loop.jsonl
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
from sandbox import SandboxUnavailable, ensure_ready


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
    turn_1_score = None  # the single-turn arm, so "extra turns helped" is a measurable claim

    # Baseline is the repository's own starter, so the local path is legitimate here.
    graded_init, err_init = grade_code(scenario, starter, trusted_repo_starter=True)
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
            # No grader-derived text in the prompt. Injecting the failing CHECK NAMES handed the
            # model the rubric (the exact adversarial inputs and the required API), so the score
            # it produced measured scorer leakage rather than the loop. profile.py:67 states the
            # same rule for the single-turn prompts: "Kept short on purpose so the rubric is not
            # leaked to the model."
            prompt = (
                f"Task: {task_desc}\n\n"
                f"Previous attempt on `{filename}` passed {best_score}/{len(best_checks)} checks.\n"
                f"Current best code for `{filename}`:\n```python\n{best_code}\n```\n\n"
                "Some required behavior is still missing or incorrect. Re-read the task, find what "
                "is still wrong, and fix it while keeping the behavior that already works. "
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
        # Model output: sandboxed, like every other model-authored file in this harness.
        graded, grade_err = grade_code(scenario, proposed_code)

        if grade_err or graded is None:
            print(f"  Turn {turn}: REVERTED (Grader error: {grade_err or 'syntax crash'})")
            history.append({"turn": turn, "action": "revert", "score": best_score, "reason": "grader_error"})
            continue

        score = sum(1 for _, ok in graded if ok)
        total = len(graded)
        if turn == 1:
            turn_1_score = score

        if score > best_score:
            print(f"  Turn {turn}: KEEP! Improved score from {best_score}/{total} to {score}/{total}")
            best_code = proposed_code
            best_score = score
            best_checks = graded
            history.append({"turn": turn, "action": "keep", "score": score, "total": total})
            if score == total:
                print(f"  [SUCCESS] All {total} checks passed on Turn {turn}!")
                return _result(scenario, model, "pass", turn, score, total, turn_1_score, history)
        else:
            print(f"  Turn {turn}: REVERTED (Hypothesis score {score}/{total} <= baseline {best_score}/{total})")
            history.append({"turn": turn, "action": "revert", "score": score, "total": total})

    outcome = "pass" if (best_checks and all(ok for _, ok in best_checks)) else "fail"
    return _result(scenario, model, outcome, len(history), best_score,
                   len(best_checks) if best_checks else 0, turn_1_score, history)


def _result(scenario, model, outcome, turns, final_score, total, turn_1_score, history) -> dict:
    return {
        "scenario": scenario, "model": model, "outcome": outcome, "turns": turns,
        "final_score": final_score, "total": total,
        # Reported so the multi-turn claim can be checked rather than asserted.
        "turn_1_score": turn_1_score,
        "rubric_free": True, "oracle_guided": True, "sandboxed": True,
        "history": history,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", help="Scenario ID (e.g. 05_security)")
    ap.add_argument("--all", action="store_true", help="Run loop simulation across all scenarios")
    ap.add_argument("--model", default="llama-3.3-70b-versatile")
    ap.add_argument("--turns", type=int, default=3)
    ap.add_argument("--api-key", help="Groq API Key override")
    ap.add_argument("--output", help="write per-scenario results as JSON Lines")
    args = ap.parse_args()

    # This runner grades model-authored files, so it needs the same sandbox precondition
    # profile.py enforces. Without this it silently executed model output on the host.
    try:
        ensure_ready()
    except SandboxUnavailable as exc:
        ap.error(str(exc))

    scenarios = sorted(TASKS) if args.all else ([args.scenario] if args.scenario else ["05_security"])
    results = []

    for sc in scenarios:
        if sc not in TASKS:
            print(f"Unknown scenario: {sc}", file=sys.stderr)
            continue
        res = run_loop_simulation(sc, model=args.model, max_turns=args.turns, api_key=args.api_key)
        results.append(res)

    if args.output:
        path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            for row in results:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        print(f"\nwrote {len(results)} rows to {path}")

    print("\n" + "=" * 60)
    print("MULTI-TURN AUTOEVOLVE SIMULATION SUMMARY")
    print("=" * 60)
    print(f"  {'scenario':16} {'outcome':7} {'turn 1':>7} {'final':>7}  turns")
    for r in results:
        first = "n/a" if r["turn_1_score"] is None else f"{r['turn_1_score']}/{r['total']}"
        print(f"  {r['scenario']:16} {r['outcome'].upper():7} {first:>7} "
              f"{f'{r['final_score']}/{r['total']}':>7}  {r['turns']}")
    print("\nBest-of-N with a graded oracle. final_score can never fall below turn 1 by")
    print("construction, so do not read the gap as evidence that keep-or-revert prevents")
    print("regressions. See this file's module docstring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
