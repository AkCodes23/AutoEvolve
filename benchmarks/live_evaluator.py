#!/usr/bin/env python3
"""Live LLM Benchmark Evaluator for AutoEvolve.

Executes actual LLM completions across prompt conditions and scores them
using deterministic AST tooling, cryptographic SHA-256 hash guards,
and pytest test runners in isolated sandboxes.

Supported Providers:
    - groq (via OpenAI-compatible endpoint)
    - openai (GPT-4o, GPT-4o-mini, o3-mini)
    - anthropic (Claude 3.5 Sonnet, Claude 3.5 Haiku)
    - ollama (local models: llama3.3, qwen2.5-coder, deepseek-r1)

Usage:
    python benchmarks/live_evaluator.py --provider ollama --model qwen2.5-coder:7b
    python benchmarks/live_evaluator.py --provider openai --model gpt-4o --scenario s1_blast_radius
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmarks.harness.runner import BenchmarkRunner

# ==============================================================================
# PROMPT LOADER
# ==============================================================================

def load_prompt_condition(condition_name: str) -> str:
    """Load the system prompt text for a given condition."""
    prompts_dir = os.path.join(REPO_ROOT, "benchmarks", "prompts")
    mapping = {
        "c0_baseline": "condition0_baseline.md",
        "c1_karpathy": "condition1_karpathy.md",
        "c2_ponytail": "condition2_ponytail.md",
        "c3_autoevolve": "condition3_autoevolve.md",
        "c5_autoevolve_praxist": "condition5_autoevolve_praxist.md",
    }

    filename = mapping.get(condition_name, f"{condition_name}.md")
    path = os.path.join(prompts_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Prompt condition file not found: {path} (condition: {condition_name})"
        )
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ==============================================================================
# LLM CLIENT ABSTRACTION
# ==============================================================================

class LLMClient:
    """Unified client for invoking LLMs across multiple backend providers."""

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        self.provider = provider.lower()
        self.timeout = timeout
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")
        self.model = model or self._default_model(self.provider)
        self.base_url = base_url or self._default_base_url(self.provider)

    @staticmethod
    def _default_model(provider: str) -> str:
        defaults = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "groq": "llama-3.3-70b-versatile",
            "ollama": "qwen2.5-coder:7b",
        }
        return defaults.get(provider, "gpt-4o")

    @staticmethod
    def _default_base_url(provider: str) -> str:
        urls = {
            "openai": "https://api.openai.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "ollama": "http://localhost:11434/v1",
            "anthropic": "https://api.anthropic.com/v1",
        }
        return urls.get(provider, "https://api.openai.com/v1")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send completion request to the configured LLM backend."""
        if self.provider in ("openai", "groq", "ollama"):
            return self._complete_openai_compatible(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._complete_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _complete_openai_compatible(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
        }

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API Error ({exc.code}): {err_body}") from exc
        except Exception as exc:
            raise RuntimeError(f"LLM Request failed: {exc}") from exc

    def _complete_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["content"][0]["text"]
        except Exception as exc:
            raise RuntimeError(f"Anthropic API Error: {exc}") from exc


# ==============================================================================
# CODE EXTRACTOR
# ==============================================================================

def extract_python_code(raw_response: str) -> str:
    """Extract Python source code from LLM Markdown fences or raw text."""
    # Match ```python ... ```
    pattern = r"```(?:python|py)?\s*\n([\s\S]*?)```"
    matches = re.findall(pattern, raw_response, re.IGNORECASE)
    if matches:
        # Return the largest code block
        return max(matches, key=len).strip()

    # Fallback: if no markdown fence, require the raw response to parse as Python.
    try:
        ast.parse(raw_response)
    except SyntaxError as exc:
        raise ValueError(
            "LLM response contains no fenced code block and is not valid Python"
        ) from exc
    return raw_response.strip()


# ==============================================================================
# LIVE BENCHMARK HARNESS
# ==============================================================================

class LiveBenchmarkHarness:
    """Runs empirical LLM evaluations across conditions with strict isolation."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client
        self.runner = BenchmarkRunner(repo_root=REPO_ROOT)
        self.results_dir = os.path.join(REPO_ROOT, "benchmarks", "results", "live")
        os.makedirs(self.results_dir, exist_ok=True)

    def evaluate_live(
        self,
        scenario_id: str,
        condition_name: str,
    ) -> Dict[str, Any]:
        """Execute a single scenario under a live LLM prompt condition."""
        if not self.client:
            raise ValueError("LLM client required for live evaluation")

        # 1. Discover scenario configuration
        scenario_cfg = None
        for sc in self.runner.list_scenarios():
            if sc.get("id") == scenario_id:
                scenario_cfg = sc
                break
        if not scenario_cfg:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        # 2. Read initial target code and test requirements
        target_rel = scenario_cfg["target_file"]
        target_abs = os.path.join(REPO_ROOT, target_rel)
        with open(target_abs, "r", encoding="utf-8") as f:
            initial_code = f.read()

        # 3. Construct prompt
        system_prompt = load_prompt_condition(condition_name)
        user_prompt = (
            f"Please solve the following software engineering task for {scenario_cfg['name']}.\n\n"
            f"Target file: `{target_rel}`\n\n"
            f"Current Implementation:\n```python\n{initial_code}\n```\n\n"
            f"Provide the complete, updated Python code that fixes the defect, adheres to all requirements, "
            f"and passes all verification tests."
        )

        # 4. Invoke LLM
        start_time = time.monotonic()
        raw_completion = self.client.complete(system_prompt, user_prompt)
        elapsed_api = time.monotonic() - start_time

        extracted_code = extract_python_code(raw_completion)

        # 5. Save raw completion for auditability
        completion_file = os.path.join(
            self.results_dir,
            f"{scenario_id}_{condition_name}_{int(time.time())}.py",
        )
        with open(completion_file, "w", encoding="utf-8") as f:
            f.write(f"# Prompt Condition: {condition_name}\n")
            f.write(f"# Scenario: {scenario_id}\n")
            f.write(f"# API Latency: {elapsed_api:.3f}s\n\n")
            f.write(extracted_code)

        # 6. Evaluate in isolated temporary sandbox
        with tempfile.TemporaryDirectory() as sandbox:
            src_benchmarks = os.path.join(REPO_ROOT, "benchmarks")
            dst_benchmarks = os.path.join(sandbox, "benchmarks")
            shutil.copytree(src_benchmarks, dst_benchmarks)

            # Apply candidate code to target file in sandbox
            sandbox_target = os.path.join(sandbox, target_rel)
            os.makedirs(os.path.dirname(sandbox_target), exist_ok=True)
            with open(sandbox_target, "w", encoding="utf-8") as f:
                f.write(extracted_code)

            # Run deterministic verification harness
            sandbox_runner = BenchmarkRunner(repo_root=sandbox)
            eval_result = sandbox_runner.evaluate_scenario(scenario_id, worktree_root=sandbox)

        return {
            "scenario_id": scenario_id,
            "condition": condition_name,
            "passed": eval_result.passed,
            "score": eval_result.score,
            "duration_seconds": eval_result.duration_seconds,
            "api_latency_seconds": round(elapsed_api, 3),
            "details": eval_result.details,
            "saved_completion": completion_file,
        }


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def run_self_test() -> int:
    """Verify that all scenarios, test harnesses, and AST evaluators work offline."""
    print("=== AutoEvolve Benchmark Harness Self-Test ===")
    runner = BenchmarkRunner(repo_root=REPO_ROOT)
    scenarios = runner.list_scenarios()
    print(f"Discovered {len(scenarios)} benchmark scenarios.")

    passed_count = 0
    completed_count = 0
    total_count = len(scenarios)

    for sc in scenarios:
        sc_id = sc["id"]
        res = runner.evaluate_scenario(sc_id)
        status = "PASS" if res.passed else "FAIL"
        print(f"  [{status}] {sc_id:<25} Score: {res.score:>5.1f}% ({res.duration_seconds:.2f}s)")
        if res.passed:
            passed_count += 1
        if res.error_message is None:
            completed_count += 1

    print("-" * 50)
    print(f"Self-Test Result: {passed_count}/{total_count} scenarios passing on baseline state.")
    print(f"Harness Health: {completed_count}/{total_count} scenarios evaluated without errors.")
    if total_count == 0 or completed_count != total_count:
        print("Self-Test FAILED: harness could not evaluate every scenario cleanly.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoEvolve Live Benchmark Evaluator")
    parser.add_argument("--self-test", action="store_true", help="Run offline self-test on all scenarios")
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic", "groq", "ollama"])
    parser.add_argument("--model", default=None, help="Model identifier (e.g. gpt-4o, qwen2.5-coder:7b)")
    parser.add_argument("--scenario", default="all", help="Scenario ID (e.g. s1_blast_radius or 'all')")
    parser.add_argument("--condition", default="all", help="Condition name (c0_baseline, c1_karpathy, c2_ponytail, c3_autoevolve, or 'all')")
    parser.add_argument("--api-key", default=None, help="Explicit API key")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    print("=== AutoEvolve Live Evaluator ===")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model or '(default)'}")

    client = LLMClient(provider=args.provider, model=args.model, api_key=args.api_key)
    harness = LiveBenchmarkHarness(client=client)

    scenarios = [s["id"] for s in harness.runner.list_scenarios()] if args.scenario == "all" else [args.scenario]
    conditions = ["c0_baseline", "c1_karpathy", "c2_ponytail", "c3_autoevolve"] if args.condition == "all" else [args.condition]

    print(f"Scenarios ({len(scenarios)}): {', '.join(scenarios)}")
    print(f"Conditions ({len(conditions)}): {', '.join(conditions)}")
    print("-" * 60)

    for sc in scenarios:
        for cond in conditions:
            print(f"Evaluating {sc} under {cond}...", end=" ", flush=True)
            try:
                res = harness.evaluate_live(sc, cond)
                status = "PASS" if res["passed"] else "FAIL"
                print(f"[{status}] Score: {res['score']}% (API: {res['api_latency_seconds']}s)")
            except Exception as exc:
                print(f"[ERROR] {exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

