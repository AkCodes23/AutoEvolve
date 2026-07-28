#!/usr/bin/env python3
"""Profile the mindset's real-world effect: does loading it help, or just add context?

This runs a controlled A/B on the eval scenarios. For each scenario it asks a model to fix
the broken starter file under conditions that differ ONLY in what instruction text is in the
system prompt:

    control  : no instructions beyond the task (just "fix this file")
    karpathy : the Karpathy coding guidelines (evals/competitors/karpathy.md)
    ponytail : the ponytail minimalism ruleset (evals/competitors/ponytail.md)
    autoevolve : the AutoEvolve mindset (AGENTS.md)

then grades the model's output with the scenario's own grader and reports the pass rate, the work
done, and the prompt-token cost per condition. If `autoevolve` does worse than `control`, the
context is making the model dumber, which is exactly what this is here to catch. The two
competitor conditions ask the harder question: does synthesizing these sources beat either source
alone?

Results are reported two ways. `strict pass` needs every check in a scenario to pass;
`graded checks` is the mean fraction of checks passed, which carries far more signal per
trial and is what you should compare when the trial budget is small.

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
import difflib
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from sandbox import SandboxUnavailable, ensure_ready, run_python

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCEN = os.path.join(ROOT, "evals", "scenarios")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Upper bound on a single honored Retry-After. A token-per-minute bucket refills within a
# few minutes, so this is a runaway guard rather than a policy.
MAX_RETRY_WAIT_SECONDS = 300

CONDITIONS = {
    "control": None,
    "karpathy": os.path.join("evals", "competitors", "karpathy.md"),
    "ponytail": os.path.join("evals", "competitors", "ponytail.md"),
    # One profile. `core` and `full` were separate arms until a measured run showed the condensed
    # one scored higher at 47 percent fewer tokens, so the longer profile was retired rather than
    # maintained alongside it. Datasets recorded before that carry `core`/`full` labels.
    "autoevolve": "AGENTS.md",
}

# A concise task per scenario, read from evals/manifest.json so the task text has ONE home.
# It used to be duplicated here and in the manifest, which is the same drift trap that let the
# docs describe three conditions while the code ran five: two copies of a fact stay equal only
# until someone edits one of them. evals/agent_benchmark.py reads the same file.
MANIFEST = os.path.join(ROOT, "evals", "manifest.json")


def _load_tasks() -> dict:
    with open(MANIFEST, encoding="utf-8") as handle:
        data = json.load(handle)
    tasks = {t["id"]: " ".join(t["task"].split()) for t in data["tasks"]}
    missing = [t for t in tasks if not os.path.isdir(os.path.join(SCEN, t))]
    if missing:
        raise SystemExit(f"manifest names scenarios that do not exist: {', '.join(sorted(missing))}")
    return tasks


TASKS = _load_tasks()

BASE_INSTRUCTION = (
    "You are a coding assistant. You are given a task and the current contents of a file. "
    "Return ONLY the complete corrected contents of that file, in a single fenced code "
    "block. Do not explain."
)

# Runs in a fresh interpreter per trial so module caching never leaks between conditions.
_SCORER = (
    "import sys, json, importlib.util, os, io, contextlib\n"
    "d = sys.argv[1]\n"
    "sys.path.insert(0, d)\n"
    "buf = io.StringIO()\n"
    "with contextlib.redirect_stdout(buf):\n"
    "    spec = importlib.util.spec_from_file_location('grade', os.path.join(d, 'grade.py'))\n"
    "    m = importlib.util.module_from_spec(spec)\n"
    "    spec.loader.exec_module(m)\n"
    "    results = [[n, bool(ok)] for n, ok, _ in m.checks()]\n"
    "print(json.dumps(results))\n"
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
    blocks = re.findall(r"```(?:[a-zA-Z0-9_+-]*\n)?(.*?)```", text, re.DOTALL)
    if blocks:
        # Take the LAST non-empty block. The prompt asks for one block holding the whole
        # corrected file; when a model emits more than one, the final block is the answer and
        # the earlier ones are reasoning or partial drafts.
        filtered = [b.strip("\n") for b in blocks if b.strip()]
        if filtered:
            return filtered[-1]
    return text.strip("\n")


def work_done(starter: str, produced: str) -> dict:
    """Measure the WORK a submission represents, not the tokens it cost to produce.

    Tokens are an input price and checks passed are an output score. Neither says anything about
    HOW the change was made, which is the only thing this project actually claims: smallest correct
    diff, deletion over addition, do not disturb what already works. Those are claims about work,
    and they are measurable from the produced source with no extra model calls.

    Returns churn (lines added plus removed), added, removed, and the fraction of the starter's
    lines still present verbatim. Two submissions that both reach full marks are not equivalent
    engineering if one changed two lines and the other rewrote the file.
    """
    before, after = starter.splitlines(), (produced or "").splitlines()
    added = removed = kept = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes():
        if tag == "equal":
            kept += i2 - i1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "insert":
            added += j2 - j1
        elif tag == "replace":
            removed += i2 - i1
            added += j2 - j1
    return {
        "churn": added + removed,
        "lines_added": added,
        "lines_removed": removed,
        "starter_lines_kept": round(kept / len(before), 4) if before else 1.0,
    }


def grade_code(
    scenario: str, code: str, *, trusted_repo_starter: bool = False
) -> tuple[list[tuple[str, bool]] | None, str | None]:
    """Grade code in the Docker sandbox.

    The parameter is named for the ONLY thing that may take the local path: a starter file the
    repository itself maintains. It defaults to False so that a caller passing model output gets
    the sandbox without having to remember to ask for it. The previous spelling was
    `sandboxed: bool = True`, which reads as safe but let any call site opt out with a keyword,
    and one did: agent_loop_sim.py passed `sandboxed=False` for raw model output.
    """
    src = os.path.join(SCEN, scenario)
    tmp = tempfile.mkdtemp(prefix="autoevolve_prof_")
    try:
        shutil.copy(os.path.join(src, "grade.py"), tmp)
        with open(os.path.join(tmp, code_file(scenario)), "w", encoding="utf-8") as f:
            f.write(code)
        if not trusted_repo_starter:
            proc = run_python(tmp, _SCORER, timeout=60)
        else:
            # Keep the environment minimal, but not so minimal that the interpreter cannot
            # start. On Windows, PATH alone is not enough: anything that initializes sockets
            # (importing asyncio, which unittest.mock pulls in) fails with
            # "WinError 10106: The requested service provider could not be loaded or
            # initialized" without SystemRoot. This path only ever runs repository starter
            # files, so the two extra variables cost nothing.
            env = {"PATH": os.environ.get("PATH", "")}
            if os.name == "nt":
                for name in ("SystemRoot", "COMSPEC", "PATHEXT"):
                    if name in os.environ:
                        env[name] = os.environ[name]
            local = subprocess.run(
                [sys.executable, "-I", "-B", "-c", _SCORER, tmp],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tmp,
                env=env,
            )
            proc = local
        if proc.returncode != 0 or not proc.stdout.strip():
            return None, (proc.stderr.strip() or f"grader exited {proc.returncode}")
        return [(n, bool(ok)) for n, ok in json.loads(proc.stdout)], None
    except SandboxUnavailable as exc:
        raise
    except Exception as exc:  # noqa: BLE001 - preserve the error for the benchmark report
        return None, type(exc).__name__
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_messages(condition_text: str | None, task: str, filename: str, code: str) -> list:
    system = BASE_INSTRUCTION
    if condition_text:
        system = condition_text.strip() + "\n\n---\n\n" + BASE_INSTRUCTION
    user = f"Task: {task}\n\nFile `{filename}`:\n```python\n{code}\n```"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def call_groq(
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int = 1400,
    base_url: str | None = None,
    api_key: str | None = None,
):
    endpoint = base_url or os.environ.get("OPENAI_BASE_URL") or GROQ_URL
    key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key and "localhost" not in endpoint and "127.0.0.1" not in endpoint:
        raise SystemExit("Set GROQ_API_KEY or OPENAI_API_KEY in environment, or specify --api-key / --base-url.")
    key = key or "dummy-key"
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    ).encode()
    req = urllib.request.Request(
        endpoint, data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
            # Groq's edge (Cloudflare) rejects the default Python-urllib User-Agent
            # with HTTP 403 (error 1010); any explicit UA gets through.
            "User-Agent": "AutoEvolve-eval/1.0",
        },
    )
    last = None
    attempts = 6
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("prompt_tokens")
            return content, tokens, None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503):
                # Honor Groq's Retry-After in full. It is the server telling us exactly when the
                # bucket refills, and it is routinely 200 seconds or more once a token-per-minute
                # allowance is exhausted.
                #
                # This used to be clamped to 30 seconds, which turned one honest wait into a
                # retry storm: sleep 30, get 429, sleep 30, ... six times, then record api_error
                # and move on, having spent six requests to accomplish nothing and pushed the
                # bucket further into deficit. Measured on an 8k-TPM model at six conditions, that
                # clamp produced a 50 percent api_error rate and silently halved the usable
                # sample. Waiting once, properly, costs the same wall clock and returns data.
                retry_after = e.headers.get("retry-after") if e.headers else None
                try:
                    wait = float(retry_after) if retry_after else 2 * (attempt + 1)
                except (TypeError, ValueError):
                    wait = 2 * (attempt + 1)
                # Clamp below by 0: a malformed negative Retry-After would otherwise reach
                # time.sleep(negative), which raises and aborts the whole run mid-loop. The upper
                # clamp is a runaway guard, not a policy: it must stay above a realistic refill.
                time.sleep(min(max(wait, 0), MAX_RETRY_WAIT_SECONDS) + 0.5)
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


def regrade(path: str) -> int:
    """Re-score a stored run against the CURRENT graders, without calling any model.

    Scores from two grader revisions are not comparable, so when a ruler is fixed the honest
    options are to re-run or to re-score. Re-running costs money and introduces fresh sampling
    noise; re-scoring the exact same stored source is free and deterministic, which makes it the
    better way to see what a grader fix did to a past result.
    """
    with open(path, encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    missing = sum(1 for r in rows if not r.get("code"))
    if missing:
        print(f"warning: {missing} of {len(rows)} rows have no stored code and are left "
              "unchanged (they predate code retention)", file=sys.stderr)
    changed = 0
    for row in rows:
        if not row.get("code"):
            continue
        graded, error = grade_code(row["scenario"], row["code"])
        if error:
            row["outcome"], row["error"] = "grader_error", error
            row["checks_passed"] = row["checks_total"] = None
            continue
        before = (row.get("checks_passed"), row.get("checks_total"))
        row["checks_passed"] = sum(1 for _, ok in graded if ok)
        row["checks_total"] = len(graded)
        row["outcome"] = "pass" if row["checks_passed"] == row["checks_total"] else "fail"
        row["error"] = None
        # Backfill the work metrics too. Rows written before churn was recorded still carry the
        # graded source, so their work axis is recoverable for free rather than lost.
        starter = read_text(os.path.join("evals", "scenarios", row["scenario"],
                                         code_file(row["scenario"])))
        row.update(work_done(starter, row["code"]))
        if before != (row["checks_passed"], row["checks_total"]):
            changed += 1
    out = path.replace(".jsonl", "") + ".regraded.jsonl"
    with open(out, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"re-scored {len(rows) - missing} rows against the current graders "
          f"({changed} changed score); wrote {out}")
    return 0


def selftest() -> int:
    print("selftest: grading each scenario's starter through the extract+grade pipeline")
    ok = True
    for scenario in sorted(TASKS):
        starter = read_text(os.path.join("evals", "scenarios", scenario, code_file(scenario)))
        wrapped = f"Here you go:\n```python\n{starter}\n```\n"
        # The only legitimate use of the local path: this input is the repository's own starter.
        graded, error = grade_code(scenario, extract_code(wrapped), trusted_repo_starter=True)
        if graded is None:
            print(f"  [ERROR] {scenario}: grader failed to run ({error or 'harness bug'})")
            ok = False
        else:
            passed = sum(1 for _, o in graded if o)
            print(f"  [ok] {scenario}: pipeline ran, {passed}/{len(graded)} checks pass on the starter")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", action="append", help="Model ID (repeatable). Avoid Qwen if you use it elsewhere.")
    ap.add_argument("--base-url", help="Custom OpenAI-compatible API endpoint (defaults to GROQ_URL or OPENAI_BASE_URL)")
    ap.add_argument("--api-key", help="API key override (defaults to GROQ_API_KEY or OPENAI_API_KEY)")
    ap.add_argument("--runs", type=int, default=3, help="trials per (scenario, condition)")
    ap.add_argument("--conditions", default="control,karpathy,ponytail,core,full")
    ap.add_argument("--scenarios", default=",".join(sorted(TASKS)))
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--min-interval", type=float, default=0.0, metavar="SECONDS",
                    help="Minimum gap between API calls, to stay UNDER the provider's "
                         "tokens-per-minute allowance instead of discovering it. Reacting to 429s "
                         "is far slower than avoiding them: an overshoot returns a Retry-After of "
                         "several minutes, so one greedy call can cost more wall clock than "
                         "pacing an entire scenario. Set it to roughly "
                         "60 * (tokens per trial) / (tokens per minute).")
    ap.add_argument("--max-tokens", type=int, default=1400,
                    help="completion cap. Raise it for scenarios whose corrected file is long: "
                         "a truncated reply grades as a failure the model did not actually make.")
    ap.add_argument("--seed", type=int, default=20260719, help="seed used to randomize trial order")
    ap.add_argument("--output", help="write trial metadata as JSON Lines for reproducible reports")
    ap.add_argument("--selftest", action="store_true", help="offline check of the grading pipeline")
    ap.add_argument("--tokens", action="store_true", help="print the context cost of each condition (no key needed)")
    ap.add_argument("--condition", action="append", default=[], metavar="NAME=PATH",
                    help="add an extra arm from a file, repeatable. This is how you test a "
                         "candidate revision of the mindset against the shipped one without "
                         "editing anything: --condition core_v2=variants/core_v2.md. Keep or "
                         "revert the revision based on the result, which is the loop this "
                         "project describes, applied to the project itself.")
    ap.add_argument("--regrade", metavar="JSONL",
                    help="re-score a previous run's stored code against the current graders. "
                         "No model calls. Use this after fixing a grader instead of paying for "
                         "the same inferences twice.")
    args = ap.parse_args()

    # Extra arms are registered before anything reads CONDITIONS, so --tokens prices them too.
    for spec in args.condition:
        name, _, path = spec.partition("=")
        name, path = name.strip(), path.strip()
        if not name or not path:
            ap.error(f"--condition expects NAME=PATH, got {spec!r}")
        if name in CONDITIONS:
            ap.error(f"--condition {name} would shadow a built-in arm; pick another name")
        if not os.path.isfile(os.path.join(ROOT, path)):
            ap.error(f"--condition {name}: no such file: {path}")
        CONDITIONS[name] = path

    if args.tokens:
        return token_report()
    if args.selftest:
        return selftest()
    if args.regrade is not None:
        # `is not None`, not truthiness: `--regrade ""` used to be falsy and fall straight through
        # to a full benchmark run, which costs real inference. An empty or missing path must fail
        # loudly rather than start spending money on something the caller did not ask for.
        if not args.regrade.strip():
            ap.error("--regrade needs a path to a results .jsonl file")
        if not os.path.isfile(args.regrade):
            ap.error(f"--regrade: no such file: {args.regrade}")
        try:
            ensure_ready()
        except SandboxUnavailable as exc:
            ap.error(str(exc))
        return regrade(args.regrade)

    models = args.model or ["llama-3.1-8b-instant"]
    conditions = [c for c in args.conditions.split(",") if c]
    scenarios = [s for s in args.scenarios.split(",") if s]
    if args.runs < 1:
        ap.error("--runs must be at least 1")
    unknown_conditions = sorted(set(conditions) - set(CONDITIONS))
    unknown_scenarios = sorted(set(scenarios) - set(TASKS))
    if unknown_conditions or unknown_scenarios:
        ap.error(f"unknown conditions={unknown_conditions}, scenarios={unknown_scenarios}")
    try:
        sandbox_image = ensure_ready()
    except SandboxUnavailable as exc:
        ap.error(str(exc))

    jobs = [
        (model, scenario, condition, trial)
        for model in models
        for scenario in scenarios
        for condition in conditions
        for trial in range(args.runs)
    ]
    random.Random(args.seed).shuffle(jobs)
    rows = []
    last_call_at = [0.0]  # monotonic timestamp of the previous API call, for --min-interval
    output_handle = None
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
        output_handle = open(args.output, "w", encoding="utf-8")
    for model, scenario, cond, trial in jobs:
        filename = code_file(scenario)
        starter = read_text(os.path.join("evals", "scenarios", scenario, filename))
        cond_text = read_text(CONDITIONS[cond]) if CONDITIONS[cond] else None
        msgs = build_messages(cond_text, TASKS[scenario], filename, starter)
        prompt_hash = hashlib.sha256(msgs[0]["content"].encode()).hexdigest()
        if args.min_interval > 0:
            gap = args.min_interval - (time.monotonic() - last_call_at[0])
            if gap > 0:
                time.sleep(gap)
        last_call_at[0] = time.monotonic()
        content, tokens, error = call_groq(model, msgs, args.temperature, max_tokens=args.max_tokens,
                                           base_url=args.base_url, api_key=args.api_key)
        outcome = "api_error" if error else "fail"
        passed_checks = checks_total = None
        graded_code = None
        if not error:
            graded_code = extract_code(content)
            graded, grade_error = grade_code(scenario, graded_code)
            if grade_error:
                outcome, error = "grader_error", grade_error
            elif graded:
                # Keep the per-check count, not just all-or-nothing. A scenario with 7 checks
                # carries 7 bits of signal; collapsing it to one pass/fail bit throws most of
                # that away and is why a binary comparison needs several times more trials to
                # detect the same effect.
                passed_checks, checks_total = sum(1 for _, ok in graded if ok), len(graded)
                if passed_checks == checks_total:
                    outcome = "pass"
        row = {
            "model": model, "scenario": scenario, "condition": cond, "trial": trial,
            "outcome": outcome, "prompt_tokens": tokens, "error": error,
            "checks_passed": passed_checks, "checks_total": checks_total,
            # The graded source is kept so a grader fix does not cost another paid inference
            # run. Graders get revised (this repo has had to void whole result sets over it),
            # and re-scoring stored code with `--regrade` is free and exactly reproducible.
            "code": graded_code,
            # Work, not price. See work_done(): churn is the size of the change, and it is the
            # only axis on which this project's central claim (smallest correct diff) is testable.
            **(work_done(starter, graded_code) if graded_code is not None else
               {"churn": None, "lines_added": None, "lines_removed": None,
                "starter_lines_kept": None}),
            "prompt_sha256": prompt_hash, "seed": args.seed,
            "temperature": args.temperature, "max_tokens": args.max_tokens,
            # Provenance travels with the result. docs/BENCHMARK.md asks for exact tool versions,
            # and the grader is a tool: recording the digest says precisely which interpreter
            # produced this verdict.
            "sandboxed": True, "sandbox_image": sandbox_image,
        }
        rows.append(row)
        # Append as we go, and flush. A long comparison is hours of paid inference, and writing
        # only at the end meant a crash, a rate-limit abort or a stopped machine threw all of it
        # away. Every completed trial is now durable the moment it finishes.
        if output_handle is not None:
            output_handle.write(json.dumps(row, sort_keys=True) + "\n")
            output_handle.flush()
        detail = f" ({tokens} prompt tokens)" if tokens else ""
        score = f" {passed_checks}/{checks_total} checks" if checks_total else ""
        print(f"  {model} {scenario} {cond} #{trial}: {outcome}{score}{detail}"
              + (f" [{error}]" if error else ""), flush=True)

    if output_handle is not None:
        output_handle.close()
    _report(models, scenarios, conditions, rows)
    return 0


def _rate(rows) -> str:
    if not rows:
        return "n/a"
    passed = sum(1 for r in rows if r["outcome"] == "pass")
    errors = sum(1 for r in rows if r["outcome"] in {"api_error", "grader_error"})
    return f"{100 * passed / len(rows):3.0f}% ({passed}/{len(rows)}, errors={errors})"


def _avg_tokens(rows):
    toks = [r["prompt_tokens"] for r in rows if r["prompt_tokens"]]
    return f"{sum(toks) // len(toks)}" if toks else "?"


def _graded(rows) -> str:
    """Mean fraction of each scenario's own checks that passed: the higher-power statistic."""
    fractions = [r["checks_passed"] / r["checks_total"] for r in rows if r.get("checks_total")]
    if not fractions:
        return "n/a"
    return f"{100 * sum(fractions) / len(fractions):3.0f}% (n={len(fractions)})"


def _churn(rows) -> str:
    """Mean lines changed. The work axis: how much of the file did it disturb to get that score?"""
    values = [r["churn"] for r in rows if r.get("churn") is not None]
    if not values:
        return "n/a"
    return f"{sum(values) / len(values):.1f}"


def _report(models, scenarios, conditions, rows):
    print("\n" + "=" * 72)
    print("PROFILE: pass rate by condition (higher is better; watch the token cost)")
    print("=" * 72)
    for model in models:
        print(f"\nmodel: {model}")
        print(f"  {'condition':10}  {'strict pass':16}  {'graded checks':16}  "
              f"{'lines changed':14}  {'avg prompt tokens':18}")
        for cond in conditions:
            sub = [r for r in rows if r["model"] == model and r["condition"] == cond]
            print(f"  {cond:10}  {_rate(sub):16}  {_graded(sub):16}  "
                  f"{_churn(sub):14}  {_avg_tokens(sub):18}")
        print(f"\n  by scenario:")
        print("  " + " " * 14 + "  ".join(f"{c:>14}" for c in conditions))
        for scenario in scenarios:
            cells = []
            for cond in conditions:
                sub = [r for r in rows if r["model"] == model and r["scenario"] == scenario and r["condition"] == cond]
                cells.append(f"{_rate(sub):>14}")
            print(f"  {scenario:14}" + "  ".join(cells))
    print("\nRead it like a signal: if 'full' does not beat 'core', the extra lines are not")
    print("earning their tokens (run --tokens for the exact cost of each condition). If")
    print("'core'/'full' trail 'control', the context is hurting. Compare the graded column:")
    print("strict pass discards most of the signal each trial carries.")
    print("\n'lines changed' is the WORK axis, and it is the one this project's central claim")
    print("lives on. Two conditions that reach the same score are not equivalent if one changed")
    print("three lines and the other rewrote the file: 'smallest correct diff' and 'deletion over")
    print("addition' are claims about churn, not about tokens or pass rates. Divide the graded")
    print("gain over the starter by the churn to compare conditions on work rather than price.")


if __name__ == "__main__":
    sys.exit(main())
