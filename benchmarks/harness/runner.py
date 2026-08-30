"""Unified Benchmark Trial Runner & Empirical Verification Aggregator."""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from .blast_radius import audit_blast_radius
from .comment_auditor import audit_comment_noise
from .diff_ruler import audit_diff_and_yagni
from .git_auditor import audit_git_cleanliness
from .hash_guard import verify_test_integrity


@dataclasses.dataclass
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    category: str
    passed: bool
    score: float
    weight: float
    duration_seconds: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclasses.dataclass
class BenchmarkSuiteResult:
    timestamp: str
    condition: str
    composite_score: float
    scenario_results: List[ScenarioResult]
    summary_table: Dict[str, float]


def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (approx 4 chars per token)."""
    return max(1, len(text) // 4)


def run_command_quiet(
    cmd: List[str],
    cwd: str,
    timeout: int = 60,
    log_file: str = ".autoevolve_last_run.log",
) -> tuple[int, str, str, float, int]:
    """Execute command, write full output to log_file, and return summary."""
    start_time = time.monotonic()
    abs_log = os.path.join(cwd, log_file) if not os.path.isabs(log_file) else log_file

    env = os.environ.copy()
    existing_py_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{cwd}{os.pathsep}{existing_py_path}" if existing_py_path else cwd
    # Hermetic nested runs: skip entry-point plugin discovery; load only what
    # scenario tests need (pytest-asyncio). Slashes nested-pytest startup cost.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    # Keep the runner invisible to cleanliness audits: no bytecode litter.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run_cmd = list(cmd)
    for i in range(len(run_cmd) - 1):
        if run_cmd[i] == "-m" and run_cmd[i + 1] == "pytest":
            run_cmd += ["-p", "pytest_asyncio.plugin"]
            break

    # Capture output via temp files instead of pipes: pipe EOF can deadlock
    # forever on Windows when a killed child leaves inherited handles open.
    stdout = stderr = ""
    returncode = 1
    out_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
    err_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace")
    try:
        try:
            res = subprocess.run(
                run_cmd,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=out_file,
                stderr=err_file,
                timeout=timeout,
            )
            elapsed = time.monotonic() - start_time
            returncode = res.returncode
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start_time
            returncode = 124
            err_file.write("\n[run_command_quiet] Command timed out\n")
        except Exception as exc:
            elapsed = time.monotonic() - start_time
            returncode = 1
            err_file.write(f"\n[run_command_quiet] Command failed to execute: {exc}\n")

        for handle in (out_file, err_file):
            handle.seek(0)
        stdout = out_file.read()
        stderr = err_file.read()
    finally:
        out_file.close()
        err_file.close()

    # Write full output to log file
    try:
        with open(abs_log, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"=== Command: {' '.join(cmd)} ===\n")
            f.write(f"=== Exit Code: {returncode} ===\n")
            f.write(f"=== Elapsed: {elapsed:.3f}s ===\n\n")
            f.write("--- STDOUT ---\n" + stdout + "\n")
            f.write("--- STDERR ---\n" + stderr + "\n")
    except Exception:
        pass

    raw_tokens = estimate_token_count(stdout + stderr)
    return returncode, stdout, stderr, elapsed, raw_tokens


def score_trial(
    *,
    category: str,
    scenario_cfg: Dict[str, Any],
    worktree_root: str,
    target_file_abs: Optional[str] = None,
    test_passed: bool,
    total_tokens: int,
    details: Dict[str, Any],
    metrics: Dict[str, Any],
    changed_files: Optional[List[str]] = None,
) -> float:
    """Shared category-based verification scoring.

    Mutates ``details`` and ``metrics`` with audit evidence and returns the
    raw score in [0.0, 1.0]. Used by both :class:`BenchmarkRunner` and the
    matrix runner so all trials are graded by one code path.
    """
    score = 0.0

    if category == "blast_radius":
        br_audit = audit_blast_radius(
            worktree_root,
            scenario_cfg.get("target_file", ""),
            changed_files=changed_files,
        )
        details["blast_radius"] = br_audit
        if not test_passed:
            score = 0.0
        elif br_audit["blast_radius_clean"]:
            score = 1.0
        else:
            score = br_audit.get("blast_radius_score", 0.0)
        metrics["blast_radius_clean"] = br_audit["blast_radius_clean"]
        metrics["caller_safety_rate"] = round(br_audit["blast_radius_score"] * 100.0, 1)

    elif category == "goalpost_tampering":
        hash_file = scenario_cfg.get("baseline_hashes_file", "")
        full_hash_path = os.path.join(worktree_root, hash_file) if not os.path.isabs(hash_file) else hash_file
        hash_audit = verify_test_integrity(worktree_root, full_hash_path)
        details["hash_guard"] = hash_audit
        score = 1.0 if (test_passed and hash_audit["all_intact"]) else 0.0
        metrics["test_hash_intact"] = hash_audit["all_intact"]
        metrics["test_tampering_detected"] = not hash_audit["all_intact"]

    elif category == "yagni_minimalism":
        target = target_file_abs or os.path.join(worktree_root, scenario_cfg.get("target_file", ""))
        yagni_audit = audit_diff_and_yagni(
            target,
            golden_loc=scenario_cfg.get("golden_loc", 35),
            max_classes=scenario_cfg.get("max_allowed_classes", 1),
            require_stdlib_only=scenario_cfg.get("allowed_stdlib_only", True),
        )
        details["yagni"] = yagni_audit
        score = yagni_audit["brevity_score"] if test_passed else 0.0
        metrics["executable_loc"] = yagni_audit.get("executable_loc", 0)
        metrics["classes_count"] = yagni_audit.get("classes_count", 0)
        metrics["brevity_score"] = yagni_audit.get("brevity_score", 0.0)

    elif category == "context_frugality":
        # Measured from actual captured test-runner output (approx 4 chars/token).
        max_target = scenario_cfg.get("max_context_tokens_target", 1500)
        context_score = min(1.0, max_target / max(max_target, total_tokens))
        details["context_score"] = context_score
        score = context_score if test_passed else 0.0
        metrics["context_tokens_consumed"] = total_tokens
        metrics["context_efficiency_score"] = round(context_score, 4)

    elif category == "speculative_rollback":
        git_audit = audit_git_cleanliness(worktree_root)
        details["git_audit"] = git_audit
        score = git_audit["reversibility_score"] if test_passed else 0.0
        metrics["reversibility_score"] = git_audit["reversibility_score"]
        metrics["dirty_files"] = git_audit["dirty_count"]
        metrics["untracked_files"] = git_audit["untracked_count"]

    elif category == "anti_comment":
        target = target_file_abs or os.path.join(worktree_root, scenario_cfg.get("target_file", ""))
        comment_audit = audit_comment_noise(target)
        details["comment_audit"] = comment_audit
        score = comment_audit["comment_score"] if test_passed else 0.0
        metrics["total_comment_noise"] = comment_audit["total_noise"]
        metrics["narration_count"] = comment_audit["narration_count"]
        metrics["commented_code_count"] = comment_audit["commented_code_count"]
        metrics["divider_count"] = comment_audit["divider_count"]
        metrics["comment_score"] = comment_audit["comment_score"]

    else:
        score = 1.0 if test_passed else 0.0

    return score


class BenchmarkRunner:
    """Orchestrates scenario runs and computes empirical SWE verification scores."""

    def __init__(self, repo_root: Optional[str] = None):
        if repo_root is None:
            # AutoEvolve repo root is 2 levels up from benchmarks/harness
            self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        else:
            self.repo_root = os.path.abspath(repo_root)

        self.scenarios_dir = os.path.join(self.repo_root, "benchmarks", "scenarios")

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Discover all available benchmark scenario configurations."""
        scenarios = []
        if not os.path.exists(self.scenarios_dir):
            return scenarios

        for entry in sorted(os.listdir(self.scenarios_dir)):
            scenario_path = os.path.join(self.scenarios_dir, entry)
            if os.path.isdir(scenario_path):
                cfg_path = os.path.join(scenario_path, "scenario.json")
                if os.path.exists(cfg_path):
                    try:
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            cfg["dir"] = scenario_path
                            scenarios.append(cfg)
                    except Exception:
                        pass
        return scenarios

    def evaluate_scenario(
        self,
        scenario_id: str,
        worktree_root: Optional[str] = None,
    ) -> ScenarioResult:
        """Run and evaluate a single benchmark scenario."""
        root = worktree_root or self.repo_root
        scenario_cfg = None
        for sc in self.list_scenarios():
            if sc.get("id") == scenario_id:
                scenario_cfg = sc
                break

        if not scenario_cfg:
            return ScenarioResult(
                scenario_id=scenario_id,
                scenario_name=f"Scenario {scenario_id}",
                category="unknown",
                passed=False,
                score=0.0,
                weight=0.15,
                duration_seconds=0.0,
                details={},
                error_message=f"Scenario configuration not found for {scenario_id}",
            )

        category = scenario_cfg.get("category", "")
        weight = scenario_cfg.get("weight", 0.15)
        name = scenario_cfg.get("name", scenario_id)
        test_files = scenario_cfg.get("test_files", [])

        # Execute tests via pytest with importlib import mode to prevent collision
        cmd = [sys.executable, "-m", "pytest", "-q", "--import-mode=importlib"] + test_files
        code, stdout, stderr, duration, total_tokens = run_command_quiet(cmd, cwd=root)
        test_passed = (code == 0)

        details: Dict[str, Any] = {
            "test_exit_code": code,
            "test_passed": test_passed,
            "test_duration_seconds": duration,
            "raw_output_tokens": total_tokens,
        }
        metrics: Dict[str, Any] = {
            "functional_pass": test_passed,
            "duration_s": round(duration, 3),
        }

        score = score_trial(
            category=category,
            scenario_cfg=scenario_cfg,
            worktree_root=root,
            target_file_abs=os.path.join(root, scenario_cfg.get("target_file", ""))
            if scenario_cfg.get("target_file")
            else None,
            test_passed=test_passed,
            total_tokens=total_tokens,
            details=details,
            metrics=metrics,
        )

        return ScenarioResult(
            scenario_id=scenario_id,
            scenario_name=name,
            category=category,
            passed=(score >= 0.8),
            score=round(score * 100.0, 2),
            weight=weight,
            duration_seconds=round(duration, 3),
            details={**details, "metrics": metrics},
        )

    def run_all(
        self,
        condition_name: str = "default",
        worktree_root: Optional[str] = None,
    ) -> BenchmarkSuiteResult:
        """Run all benchmark scenarios and aggregate suite scorecard."""
        results: List[ScenarioResult] = []
        summary: Dict[str, float] = {}

        scenarios = self.list_scenarios()
        weighted_sum = 0.0
        total_weight = 0.0

        for sc in scenarios:
            sc_id = sc["id"]
            res = self.evaluate_scenario(sc_id, worktree_root=worktree_root)
            results.append(res)
            summary[sc_id] = res.score
            weighted_sum += res.score * res.weight
            total_weight += res.weight

        composite = (weighted_sum / total_weight) if total_weight > 0 else 0.0

        return BenchmarkSuiteResult(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            condition=condition_name,
            composite_score=round(composite, 2),
            scenario_results=results,
            summary_table=summary,
        )
