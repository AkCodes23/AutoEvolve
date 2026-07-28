"""Deterministic regression tests for profiler accounting and sandbox configuration.

Several of these pin SAFETY CONTROLS rather than behavior. They exist because the repository
once shipped a runner that graded model-authored code directly on the host while every document
promised sandboxed grading, and the invariant suite was green the whole time. A control with no
test is a control that will be removed by the next refactor.
"""
from __future__ import annotations

import inspect
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
import agent_benchmark  # noqa: E402
import agent_loop_sim  # noqa: E402
import profile  # noqa: E402
import sandbox  # noqa: E402


class ProfileTests(unittest.TestCase):
    def test_extract_code_uses_last_fenced_block(self) -> None:
        self.assertEqual(profile.extract_code("```python\na = 1\n```\n```\nb = 2\n```"), "b = 2")

    def test_rate_counts_errors_in_the_denominator(self) -> None:
        rows = [
            {"outcome": "pass", "prompt_tokens": 10},
            {"outcome": "fail", "prompt_tokens": 10},
            {"outcome": "api_error", "prompt_tokens": None},
        ]
        self.assertEqual(profile._rate(rows), " 33% (1/3, errors=1)")

    def test_graded_score_uses_per_check_fractions(self) -> None:
        rows = [
            {"checks_passed": 3, "checks_total": 6},
            {"checks_passed": 6, "checks_total": 6},
            {"checks_passed": None, "checks_total": None},  # an error row contributes nothing
        ]
        self.assertEqual(profile._graded(rows), " 75% (n=2)")

    def test_work_done_measures_churn_not_size(self) -> None:
        # The work axis. An unchanged submission must cost zero, or "did nothing" would look like
        # the most efficient possible answer.
        starter = "def f():\n    return 1\n\ndef g():\n    return 2\n"
        self.assertEqual(profile.work_done(starter, starter)["churn"], 0)
        self.assertEqual(profile.work_done(starter, starter)["starter_lines_kept"], 1.0)

        one_line = profile.work_done(starter, starter.replace("return 1", "return 99"))
        self.assertEqual(one_line["churn"], 2)  # one line out, one line in
        self.assertEqual(one_line["lines_added"], 1)
        self.assertEqual(one_line["lines_removed"], 1)

        # Deletion is credited as work, and this project prefers it: "deletion over addition".
        deleted = profile.work_done(starter, "def f():\n    return 1\n")
        self.assertEqual(deleted["lines_added"], 0)
        self.assertEqual(deleted["lines_removed"], 3)

        # A rewrite must cost more churn than a surgical edit at the same file size.
        rewrite = profile.work_done(starter, "def f():\n    return 99\n\ndef g():\n    return 42\n")
        self.assertGreater(rewrite["churn"], one_line["churn"])

    def test_conditions_include_both_competitor_baselines(self) -> None:
        # The project's central claim is that the synthesis beats the sources it synthesizes,
        # which is unmeasurable if the competitor arms are missing from a harness.
        for harness in (profile.CONDITIONS, agent_benchmark.CONDITIONS):
            self.assertIn("karpathy", harness)
            self.assertIn("ponytail", harness)

    def test_exactly_one_autoevolve_profile(self) -> None:
        # One profile, deliberately. `core` and `full` were separate arms until a measured run
        # scored the condensed one higher at far fewer tokens; keeping both meant maintaining two
        # copies of the same rules, which is how they drift.
        for harness in (profile.CONDITIONS, agent_benchmark.CONDITIONS):
            ours = [name for name in harness if name not in ("control", "karpathy", "ponytail")]
            self.assertEqual(ours, ["autoevolve"], f"expected one AutoEvolve arm, got {ours}")
        self.assertEqual(profile.CONDITIONS["autoevolve"], "AGENTS.md")

    def test_adapters_are_generated_from_agents_md(self) -> None:
        # The adapters must be byte-identical to AGENTS.md plus their frontmatter, so there is one
        # place to edit the mindset. Compared as bytes: a text-mode compare hid a CRLF/LF mismatch.
        sys.path.insert(0, os.path.join(profile.ROOT, "scripts"))
        import build_adapters
        self.assertEqual(build_adapters.build(check=True), [],
                         "adapters are stale; run python3 scripts/build_adapters.py")
        self.assertFalse(os.path.exists(os.path.join(profile.ROOT, "adapters", "_core.md")),
                         "the second profile was retired; adapters/_core.md must not come back")

    def test_every_condition_file_exists(self) -> None:
        for name, path in profile.CONDITIONS.items():
            if path is None:
                continue
            self.assertTrue(os.path.exists(os.path.join(profile.ROOT, path)), f"{name} -> {path}")

    def test_tasks_come_from_the_manifest_and_cover_every_scenario(self) -> None:
        # One home for the task text. Both harnesses read this file, so a scenario added to the
        # manifest is picked up everywhere, and a scenario directory with no manifest entry is a
        # scenario the benchmark silently skips.
        on_disk = {d for d in os.listdir(profile.SCEN)
                   if os.path.isdir(os.path.join(profile.SCEN, d)) and not d.startswith((".", "__"))}
        self.assertEqual(set(profile.TASKS), on_disk,
                         "evals/manifest.json and evals/scenarios/ disagree about the suite")
        for scenario, text in profile.TASKS.items():
            self.assertTrue(text.strip(), f"{scenario} has an empty task")
            self.assertNotIn("\n", text, f"{scenario} task should be one normalized line")


class SandboxControlTests(unittest.TestCase):
    """These four pin the boundary between trusted repository files and model output."""

    def test_sandbox_requires_a_digest_pinned_image(self) -> None:
        with patch.dict(os.environ, {sandbox.IMAGE_ENV: "python:3.12-alpine"}, clear=True):
            with self.assertRaises(sandbox.SandboxUnavailable):
                sandbox._image_reference()

    def test_grade_code_defaults_to_the_sandbox(self) -> None:
        # A caller that forgets to think about isolation must get the sandbox anyway.
        signature = inspect.signature(profile.grade_code)
        self.assertIs(signature.parameters["trusted_repo_starter"].default, False)

    def test_model_output_is_routed_to_the_sandbox(self) -> None:
        # Assert the routing rather than a raised error: grade_code catches broad Exception and
        # converts it into an error tuple, so a probe that raises would be silently absorbed.
        graded = sandbox.SandboxResult(stdout='[["check", true]]', stderr="", returncode=0)
        with patch.object(profile, "run_python", return_value=graded) as sandboxed:
            with patch.object(profile.subprocess, "run") as host:
                profile.grade_code("07_yagni", "x = 1")
        self.assertTrue(sandboxed.called, "model output must be graded in the sandbox")
        self.assertFalse(host.called, "model output must never be graded by a host subprocess")

    def test_trusted_repo_starter_takes_the_local_path(self) -> None:
        with patch.object(profile, "run_python") as sandboxed:
            profile.grade_code("07_yagni", "def parse_tags(text):\n    return []\n",
                               trusted_repo_starter=True)
        self.assertFalse(sandboxed.called)

    def test_loop_sim_grades_model_output_in_the_sandbox(self) -> None:
        # The regression this repository actually shipped: agent_loop_sim.py passed
        # sandboxed=False for raw model output, so it never entered a container at all.
        source = inspect.getsource(agent_loop_sim)
        self.assertNotIn("sandboxed=False", source)
        self.assertIn("trusted_repo_starter=True", source)  # the baseline starter, and only that
        self.assertEqual(source.count("trusted_repo_starter=True"), 1)

    def test_loop_sim_prompt_does_not_leak_the_rubric(self) -> None:
        # Feeding the grader's check names back into the prompt hands the model the answer key.
        source = inspect.getsource(agent_loop_sim.run_loop_simulation)
        self.assertNotIn("Failing checks", source)


class BenchmarkRunnerTests(unittest.TestCase):
    def test_runner_environment_withholds_credentials(self) -> None:
        secrets = {"GROQ_API_KEY": "x", "ANTHROPIC_API_KEY": "x", "GITHUB_TOKEN": "x",
                   "AWS_SECRET_ACCESS_KEY": "x", "PATH": "/usr/bin"}
        with patch.dict(os.environ, secrets, clear=True):
            env = agent_benchmark.runner_environment(__file__, "control", [])
        for leaked in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY"):
            self.assertNotIn(leaked, env)
        self.assertIn("PATH", env)
        self.assertEqual(env["AUTOEVOLVE_CONDITION"], "control")

    def test_runner_environment_honors_explicit_passthrough(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "x", "PATH": "/usr/bin"}, clear=True):
            env = agent_benchmark.runner_environment(__file__, "core", ["GROQ_API_KEY"])
        self.assertEqual(env["GROQ_API_KEY"], "x")


if __name__ == "__main__":
    unittest.main()
