#!/usr/bin/env python3
"""Benchmark a real tool-using agent against isolated repository tasks.

The configured runner is intentionally tool-agnostic. It is a user-authorized command that
receives a disposable task checkout as its working directory and the task path in
AUTOEVOLVE_TASK_PATH. Generated code is graded only in the Docker sandbox.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from sandbox import SandboxUnavailable, ensure_ready, run_python


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {"control": None, "core": ROOT / "adapters" / "_core.md", "full": ROOT / "AGENTS.md"}
SCORER = (
    "import sys, json, importlib.util, os\n"
    "d = sys.argv[1]\n"
    "sys.path.insert(0, d)\n"
    "spec = importlib.util.spec_from_file_location('grade', os.path.join(d, 'grade.py'))\n"
    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
    "print(json.dumps([[n, bool(ok)] for n, ok, _ in m.checks()]))\n"
)


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("manifest must contain a non-empty tasks array")
    required = {"id", "source", "task", "code_file"}
    for task in tasks:
        if not required.issubset(task):
            raise ValueError(f"task is missing required fields: {required - set(task)}")
    return tasks


def source_path(task: dict) -> Path:
    source = (ROOT / task["source"]).resolve()
    if ROOT not in source.parents or not source.is_dir():
        raise ValueError(f"task source escapes repository or is missing: {task['source']}")
    return source


def grade(task: dict, agent_workspace: Path) -> tuple[bool | None, str | None]:
    source = source_path(task)
    grade_workspace = Path(tempfile.mkdtemp(prefix="autoevolve_grade_"))
    try:
        shutil.copy2(source / "grade.py", grade_workspace / "grade.py")
        shutil.copy2(agent_workspace / task["code_file"], grade_workspace / task["code_file"])
        result = run_python(str(grade_workspace), SCORER)
        if result.returncode or not result.stdout.strip():
            return None, result.stderr.strip() or f"grader exited {result.returncode}"
        checks = json.loads(result.stdout)
        return all(ok for _, ok in checks), None
    except Exception as exc:  # noqa: BLE001 - retain failures in benchmark metadata
        return None, type(exc).__name__
    finally:
        shutil.rmtree(grade_workspace, ignore_errors=True)


def run_trial(task: dict, condition: str, runner: list[str], timeout: int) -> tuple[str, str | None]:
    source = source_path(task)
    workspace = Path(tempfile.mkdtemp(prefix="autoevolve_agent_"))
    try:
        shutil.copytree(source, workspace / "repo", ignore=shutil.ignore_patterns("grade.py"))
        repo = workspace / "repo"
        task_path = repo / "TASK.md"
        task_path.write_text(task["task"].strip() + "\n", encoding="utf-8")
        instruction = CONDITIONS[condition]
        if instruction:
            shutil.copy2(instruction, repo / "AGENTS.md")
        environment = os.environ.copy()
        environment.update({"AUTOEVOLVE_TASK_PATH": str(task_path), "AUTOEVOLVE_CONDITION": condition})
        try:
            process = subprocess.run(runner, cwd=repo, env=environment, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return "runner_error", "runner timeout"
        if process.returncode:
            return "runner_error", f"runner exited {process.returncode}"
        passed, error = grade(task, repo)
        if error:
            return "grader_error", error
        return ("pass" if passed else "fail"), None
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--runner", required=True, help="agent command; executed without a shell")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--seed", type=int, default=20260719)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.runs < 1 or args.timeout < 1:
        parser.error("--runs and --timeout must be positive")
    try:
        ensure_ready()
        tasks = load_manifest(args.manifest)
    except (SandboxUnavailable, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    runner = shlex.split(args.runner, posix=os.name != "nt")
    if not runner:
        parser.error("--runner must contain a command")
    jobs = [(task, condition, trial) for task in tasks for condition in CONDITIONS for trial in range(args.runs)]
    random.Random(args.seed).shuffle(jobs)
    rows = []
    for task, condition, trial in jobs:
        outcome, error = run_trial(task, condition, runner, args.timeout)
        row = {"task": task["id"], "condition": condition, "trial": trial, "outcome": outcome,
               "error": error, "seed": args.seed}
        rows.append(row)
        print(f"{task['id']} {condition} #{trial}: {outcome}" + (f" [{error}]" if error else ""))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    for condition in CONDITIONS:
        subset = [r for r in rows if r["condition"] == condition]
        passed = sum(r["outcome"] == "pass" for r in subset)
        errors = sum(r["outcome"] != "pass" and r["outcome"] != "fail" for r in subset)
        print(f"{condition}: {passed}/{len(subset)} passed, errors={errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
