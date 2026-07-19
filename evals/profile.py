#!/usr/bin/env python3
"""Profile the mindset's real-world effect: does loading it help, or just add context?

This runs a controlled A/B on the eval scenarios. For each scenario it asks a model to fix
the broken starter file under three conditions that differ ONLY in how much mindset text is
in the system prompt:

    control : no mindset (just "fix this file")
    core    : the ~25-line condensed core (adapters/_core.md)
    full    : the full AGENTS.md (~150 lines)

then grades the model's output with the scenario's own grader and reports the pass rate and
the average prompt-token cost per condition. If `full` does not beat `core`, the extra
context is not earning its tokens. If `core`/`full` do worse than `control`, the context is
making the model dumber, which is exactly what this is here to catch.

Uses Groq's OpenAI-compatible API (small models show the effect most clearly). Standard
library only. Set your key first, and do not commit it:

    export GROQ_API_KEY=...            # never hard-code this
    python3 evals/profile.py                                  # defaults: one small model, 3 runs
    python3 evals/profile.py --model llama-3.3-70b-versatile --runs 5
    python3 evals/profile.py --selftest                       # offline: verify the grading pipeline

Note: pick non-Qwen models if you use Qwen elsewhere. This never runs in CI (it costs API
calls); it is an on-demand experiment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN = os.path.join(ROOT, "evals", "scenarios")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CONDITIONS = {
    "control": None,
    "core": os.path.join("adapters", "_core.md"),
    "full": "AGENTS.md",
}

# A concise task per scenario. Kept short on purpose so the rubric is not leaked to the model.
TASKS = {
    "01_bugfix": (
        "search('') crashes instead of returning an empty list. search is also called by "
        "suggest, count_matches, and has_match. Fix it so an empty query returns empty "
        "results through every caller, and valid queries still work."
    ),
    "02_optimize": (
        "dedupe(items) removes duplicates while preserving order but is O(n^2). Make it run "
        "in linear time without changing its behavior or output order."
    ),
    "03_feature": (
        "Add a `page` parameter to list_items (1-based, per_page default 10). With no page, "
        "return all items exactly as before. With page=N, return that page. Reject an invalid "
        "page (zero, negative, or non-integer)."
    ),
}

BASE_INSTRUCTION = (
    "You are a coding assistant. You are given a task and the current contents of a file. "
    "Return ONLY the complete corrected contents of that file, in a single fenced code "
    "block. Do not explain."
)

# Runs in a fresh interpreter per trial so module caching never leaks between conditions.
_SCORER = (
    "import sys, json, importlib.util, os\n"
    "d = sys.argv[1]\n"
    "sys.path.insert(0, d)\n"
    "spec = importlib.util.spec_from_file_location('grade', os.path.join(d, 'grade.py'))\n"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
    "print(json.dumps([[n, bool(ok)] for n, ok, _ in m.checks()]))\n"
)


def read_text(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def code_file(scenario: str) -> str:
    """The single .py under test in a scenario dir (the one that is not grade.py)."""
    for name in sorted(os.listdir(os.path.join(SCEN, scenario))):
        if name.endswith(".py") and name != "grade.py":
            return name
    raise FileNotFoundError(f"no code-under-test file in {scenario}")


def extract_code(text: str) -> str:
    blocks = re.findall(r"```[a-zA-Z0-9_+-]*\n(.*?)```", text, re.DOTALL)
    return (blocks[-1] if blocks else text).strip("\n")


def grade_code(scenario: str, code: str) -> list[tuple[str, bool]] | None:
    """Write `code` into a throwaway copy of the scenario and grade it. None on grader error."""
    src = os.path.join(SCEN, scenario)
    tmp = tempfile.mkdtemp(prefix="autoevolve_prof_")
    try:
        shutil.copy(os.path.join(src, "grade.py"), tmp)
        with open(os.path.join(tmp, code_file(scenario)), "w", encoding="utf-8") as f:
            f.write(code)
        proc = subprocess.run(
            [sys.executable, "-c", _SCORER, tmp], capture_output=True, text=True, timeout=60
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        return [(n, bool(ok)) for n, ok in json.loads(proc.stdout)]
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_messages(condition_text: str | None, task: str, filename: str, code: str) -> list:
    system = BASE_INSTRUCTION
    if condition_text:
        system = condition_text.strip() + "\n\n---\n\n" + BASE_INSTRUCTION
    user = f"Task: {task}\n\nFile `{filename}`:\n```python\n{code}\n```"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def call_groq(model: str, messages: list, temperature: float, max_tokens: int = 1400):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise SystemExit("Set GROQ_API_KEY in your environment (do not commit it).")
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    ).encode()
    req = urllib.request.Request(
        GROQ_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
    )
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("prompt_tokens")
            return content, tokens, None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503):
                time.sleep(2 * (attempt + 1))
                continue
            return None, None, last
        except Exception as e:  # noqa: BLE001 - report any transport error, keep going
            last = f"{type(e).__name__}"
            time.sleep(2 * (attempt + 1))
    return None, None, last


def token_report() -> int:
    """Print the always-on context cost of each condition. No network, no key."""
    print("Context cost per condition (rough estimate, ~chars / 4):")
    print(f"  {'condition':10} {'chars':>7} {'words':>7} {'~tokens':>8}")
    for cond, path in CONDITIONS.items():
        if path is None:
            print(f"  {cond:10} {0:>7} {0:>7} {0:>8}")
            continue
        text = read_text(path)
        print(f"  {cond:10} {len(text):>7} {len(text.split()):>7} {len(text) // 4:>8}")
    print("\nThis is the cost half of the question (how many tokens you pay every turn).")
    print("The accuracy half needs a model: run without --tokens (set GROQ_API_KEY).")
    return 0


def selftest() -> int:
    print("selftest: grading each scenario's starter through the extract+grade pipeline")
    ok = True
    for scenario in sorted(TASKS):
        starter = read_text(os.path.join("evals", "scenarios", scenario, code_file(scenario)))
        wrapped = f"Here you go:\n```python\n{starter}\n```\n"
        graded = grade_code(scenario, extract_code(wrapped))
        if graded is None:
            print(f"  [ERROR] {scenario}: grader failed to run (harness bug)")
            ok = False
        else:
            passed = sum(1 for _, o in graded if o)
            print(f"  [ok] {scenario}: pipeline ran, {passed}/{len(graded)} checks pass on the starter")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", action="append", help="Groq model id (repeatable). Avoid Qwen if you use it elsewhere.")
    ap.add_argument("--runs", type=int, default=3, help="trials per (scenario, condition)")
    ap.add_argument("--conditions", default="control,core,full")
    ap.add_argument("--scenarios", default=",".join(sorted(TASKS)))
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--selftest", action="store_true", help="offline check of the grading pipeline")
    ap.add_argument("--tokens", action="store_true", help="print the context cost of each condition (no key needed)")
    args = ap.parse_args()

    if args.tokens:
        return token_report()
    if args.selftest:
        return selftest()

    models = args.model or ["llama-3.1-8b-instant"]
    conditions = [c for c in args.conditions.split(",") if c]
    scenarios = [s for s in args.scenarios.split(",") if s]
    rows = []  # (model, scenario, condition, trial, passed, prompt_tokens, error)

    for model in models:
        for scenario in scenarios:
            filename = code_file(scenario)
            starter = read_text(os.path.join("evals", "scenarios", scenario, filename))
            task = TASKS[scenario]
            for cond in conditions:
                cond_text = read_text(CONDITIONS[cond]) if CONDITIONS[cond] else None
                for trial in range(args.runs):
                    msgs = build_messages(cond_text, task, filename, starter)
                    content, tokens, err = call_groq(model, msgs, args.temperature)
                    if err:
                        rows.append((model, scenario, cond, trial, None, tokens, err))
                        print(f"  {model} {scenario} {cond} #{trial}: API error {err}")
                        continue
                    graded = grade_code(scenario, extract_code(content))
                    passed = bool(graded) and all(ok for _, ok in graded)
                    rows.append((model, scenario, cond, trial, passed, tokens, None))
                    print(f"  {model} {scenario} {cond} #{trial}: {'PASS' if passed else 'fail'}"
                          f"  ({tokens} prompt tokens)")

    _report(models, scenarios, conditions, rows)
    return 0


def _rate(rows) -> str:
    graded = [r for r in rows if r[4] is not None]
    if not graded:
        return "n/a"
    passed = sum(1 for r in graded if r[4])
    return f"{100 * passed / len(graded):3.0f}% ({passed}/{len(graded)})"


def _avg_tokens(rows):
    toks = [r[5] for r in rows if r[5]]
    return f"{sum(toks) // len(toks)}" if toks else "?"


def _report(models, scenarios, conditions, rows):
    print("\n" + "=" * 72)
    print("PROFILE: pass rate by condition (higher is better; watch the token cost)")
    print("=" * 72)
    for model in models:
        print(f"\nmodel: {model}")
        print(f"  {'condition':10}  {'overall':16}  {'avg prompt tokens':18}")
        for cond in conditions:
            sub = [r for r in rows if r[0] == model and r[2] == cond]
            print(f"  {cond:10}  {_rate(sub):16}  {_avg_tokens(sub):18}")
        print(f"\n  by scenario:")
        print("  " + " " * 14 + "  ".join(f"{c:>14}" for c in conditions))
        for scenario in scenarios:
            cells = []
            for cond in conditions:
                sub = [r for r in rows if r[0] == model and r[1] == scenario and r[2] == cond]
                cells.append(f"{_rate(sub):>14}")
            print(f"  {scenario:14}" + "  ".join(cells))
    print("\nRead it like a signal: if 'full' does not beat 'core', the extra ~125 lines are")
    print("not earning their tokens. If 'core'/'full' trail 'control', the context is hurting.")


if __name__ == "__main__":
    sys.exit(main())
