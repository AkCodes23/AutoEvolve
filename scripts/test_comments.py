"""Calibration tests for the comment-noise reporter.

The point of this file is the FALSE POSITIVE half. A reporter that flags a comment recording a
measured result is worse than no reporter: it trains you to skim past the output, and the
comments it would have you delete are the most expensive text in a repository. So every
detector is pinned twice, once on text it must flag and once on text it must not, and the
must-not cases are taken verbatim from this repository's own source.
"""
from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comments  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_source(source: str) -> list[tuple[int, str, str]]:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(textwrap.dedent(source))
        return comments.scan(path)


def tiers(source: str) -> list[str]:
    return [tier for _, tier, _ in scan_source(source)]


class CommentedOutCodeTests(unittest.TestCase):
    def test_flags_disabled_statements(self) -> None:
        for body in ["import json", "x = compute(1)", "print(user)", "self.cache = {}",
                     "return None", "for row in rows:\n    pass", "del cache[key]",
                     "raise ValueError('nope')", "result += 1", "await fetch(url)"]:
            self.assertTrue(comments.is_commented_out_code(body), body)

    def test_does_not_flag_prose(self) -> None:
        prose = [
            "Fix at the root rather than patching each call site",
            "import the module before you read the config",
            "global state is rebuilt on every run",
            "for each row, check the total",
            "return the count, or None when the catalog is empty",
            "delete this once the migration lands",
            "raise the cap only after measuring",
            "See build_adapters.py for the generated form",
            "python3 scripts/callers.py --rev HEAD~3",
            "e.g. parse_tags(\"a, b\") drops the empty entry",
            "TODO", "ok", "noqa", "n", "why",
        ]
        for body in prose:
            self.assertFalse(comments.is_commented_out_code(body), body)


class DividerTests(unittest.TestCase):
    def test_flags_decoration(self) -> None:
        for body in ["=" * 40, "-------------", "### Section ###", "---- helpers ----", "****"]:
            self.assertTrue(comments.is_divider(body), body)

    def test_does_not_flag_sentences_containing_dashes(self) -> None:
        for body in ["a - b is negative when b wins", "step 1 -> step 2", "--rev is optional"]:
            self.assertFalse(comments.is_divider(body), body)


class VacuousDocstringTests(unittest.TestCase):
    def test_flags_a_docstring_rebuilt_from_the_signature(self) -> None:
        self.assertEqual(tiers('''
            def get_user_name(user):
                """Get the user name."""
                return user.name
        '''), ["noise"])

    def test_keeps_a_docstring_that_adds_information(self) -> None:
        self.assertEqual(tiers('''
            def median_of(samples):
                """An outlier moves a mean, not a median, so noisy signals use the middle."""
                return sorted(samples)[len(samples) // 2]
        '''), [])

    def test_keeps_a_multiline_docstring(self) -> None:
        self.assertEqual(tiers('''
            def get_user(user):
                """Get the user.

                Longer text is left alone: the summary line is a convention, not noise.
                """
                return user
        '''), [])


class RestatementTests(unittest.TestCase):
    def test_flags_a_comment_restating_the_next_line(self) -> None:
        self.assertEqual(tiers("""
            # increment the counter
            counter = counter + 1
        """), ["candidate"])

    def test_flags_a_trailing_comment_restating_its_own_line(self) -> None:
        self.assertEqual(tiers("""
            total = sum(items)  # sum the items
        """), ["candidate"])

    def test_keeps_a_comment_that_records_a_why(self) -> None:
        self.assertEqual(tiers("""
            # A single slow run is the machine, not the change, so take the middle value.
            ordered = sorted(samples)
        """), [])


class ExemptionTests(unittest.TestCase):
    def test_work_markers_and_directives_are_left_alone(self) -> None:
        self.assertEqual(tiers("""
            # TODO: handle negative amounts
            # FIXME: this drops the tail
            # type: ignore
            # noqa: E501
            # evolve: O(n^2) scan, fine under 10k rows; use a hash index above
            value = 1
        """), [])


class StrictTierTests(unittest.TestCase):
    def test_candidates_alone_never_fail_strict(self) -> None:
        """--strict is for hooks, so only provable noise may block a commit."""
        found = scan_source("""
            # increment the counter
            counter = counter + 1
        """)
        self.assertTrue(found)
        self.assertNotIn("noise", [tier for _, tier, _ in found])


class RepositoryCalibrationTests(unittest.TestCase):
    """The reporter must stay silent on this repository's own why-comments.

    These files carry postmortems of real incidents (the `git checkout -- .` data loss in
    autoevolve.py, the same-module caller blind spot in callers.py). If a change to the
    detectors starts flagging them, the detectors are wrong, not the comments.
    """

    FILES = ["autoevolve.py", "scripts/callers.py", "scripts/check.py", "scripts/comments.py",
             "scripts/branch.py", "scripts/run_quiet.py", "scripts/build_adapters.py",
             "evals/profile.py", "evals/sandbox.py", "evals/work_report.py",
             "evals/agent_benchmark.py", "evals/agent_loop_sim.py"]

    def test_no_noise_in_the_repositorys_own_sources(self) -> None:
        offenders = []
        for rel in self.FILES:
            for line, tier, message in comments.scan(os.path.join(ROOT, rel)):
                if tier == "noise":
                    offenders.append(f"{rel}:{line}  {message}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
