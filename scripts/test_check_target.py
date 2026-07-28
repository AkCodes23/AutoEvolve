"""Tests for target readiness detection.

The point of this file is that `setup` and `check` must agree. They had two independent tables:
`setup` counted a bare `tests/` directory as pytest and wrote "pytest tests/" into DIRECTION.md,
`check` did not, so `check` reported "Test Runner: None" for a repo `setup` had just configured.
One command contradicting another about the same directory is worse than either answer alone.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_target  # noqa: E402


def repo(*entries: str) -> str:
    """A throwaway directory containing the named files and directories."""
    tmp = tempfile.mkdtemp()
    for entry in entries:
        path = os.path.join(tmp, entry)
        if entry.endswith("/"):
            os.makedirs(path, exist_ok=True)
        else:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("")
    return tmp


class DetectionTests(unittest.TestCase):
    def test_a_marker_file_names_its_runner(self) -> None:
        for marker, stack, command in [("pytest.ini", "python/pytest", "pytest"),
                                       ("package.json", "javascript/npm", "npm test"),
                                       ("Cargo.toml", "rust/cargo", "cargo test"),
                                       ("go.mod", "go/modules", "go test ./..."),
                                       ("Makefile", "make/c", "make test")]:
            stacks, suggested = check_target.detect_signal(repo(marker))
            self.assertEqual((stacks, suggested), ([stack], command), marker)

    def test_a_bare_tests_directory_counts(self) -> None:
        stacks, command = check_target.detect_signal(repo("tests/"))
        self.assertEqual((stacks, command), (["python/pytest"], "pytest tests/"))

    def test_nothing_detected_returns_no_command(self) -> None:
        """An invented signal is worse than an empty one a human has to fill in."""
        self.assertEqual(check_target.detect_signal(repo("README.md")), ([], None))

    def test_a_marker_file_wins_over_a_bare_directory(self) -> None:
        _, command = check_target.detect_signal(repo("pytest.ini", "tests/"))
        self.assertEqual(command, "pytest")

    def test_a_stack_is_not_reported_twice(self) -> None:
        stacks, _ = check_target.detect_signal(repo("pyproject.toml", "tests/"))
        self.assertEqual(stacks, ["python/pytest"])


class AgreementTests(unittest.TestCase):
    """The regression this file exists for: the two commands must not disagree."""

    def test_setup_and_check_agree_on_every_case(self) -> None:
        for entries in [("tests/",), ("pytest.ini",), ("package.json",), ("go.mod",),
                        ("Cargo.toml",), ("Makefile",), ("README.md",)]:
            target = repo(*entries)
            stacks, command = check_target.detect_signal(target)
            found = check_target.check_target(target)["has_test_runner"]
            self.assertEqual(found, bool(command), entries)
            self.assertEqual(found, bool(stacks), entries)

    def test_setup_uses_the_shared_detector_rather_than_its_own_table(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "autoevolve.py"), encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("from check_target import detect_signal", source)
        self.assertNotIn('detected = "pytest tests/"', source)


if __name__ == "__main__":
    unittest.main()
