"""Tests for the AutoEvolve CLI, concentrated on the loop's argument parsing.

`loop` is the one command that can throw away work, so a parse it accepts but misreads is worse
here than anywhere else in the toolkit. This file exists because of one such parse: `--paths` took
a single value per flag while `callers.py`, `comments.py` and `ruler.py` all take several, so
`--paths a.py b.py` silently pushed `b.py` into the verification COMMAND. The command failed
because a .py file is not an executable, the loop announced SIGNAL REGRESSED, and it reverted
a.py. The user was told their change made things worse and lost it, over a flag.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, "autoevolve.py")


def git(args: list[str], cwd: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False)


def repo() -> str:
    tmp = tempfile.mkdtemp()
    for name in ("a.py", "b.py"):
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
            handle.write("original\n")
    git(["init", "-q", "."], tmp)
    git(["config", "user.email", "t@t.t"], tmp)
    git(["config", "user.name", "t"], tmp)
    git(["add", "-A"], tmp)
    git(["commit", "-qm", "base"], tmp)
    for name in ("a.py", "b.py"):
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
            handle.write("changed\n")
    return tmp


def loop(cwd: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, CLI, "loop", "--target", cwd, *args],
                          capture_output=True, text=True)


def body(cwd: str, name: str) -> str:
    with open(os.path.join(cwd, name), encoding="utf-8") as handle:
        return handle.read()


class PathParsingTests(unittest.TestCase):
    OK = ["--", sys.executable, "-c", "pass"]
    FAIL = ["--", sys.executable, "-c", "import sys; sys.exit(1)"]

    def test_several_paths_after_one_flag(self) -> None:
        """The regression: this used to run `b.py` as the command and revert a.py."""
        cwd = repo()
        result = loop(cwd, "--paths", "a.py", "b.py", *self.OK)
        self.assertIn("PASS", result.stdout)
        self.assertNotIn("b.py python", result.stdout)
        self.assertEqual(body(cwd, "a.py"), "changed\n")
        self.assertEqual(body(cwd, "b.py"), "changed\n")

    def test_the_flag_may_still_be_repeated(self) -> None:
        cwd = repo()
        self.assertIn("PASS", loop(cwd, "--paths", "a.py", "--paths", "b.py", *self.OK).stdout)

    def test_a_failing_signal_reverts_every_declared_path(self) -> None:
        cwd = repo()
        loop(cwd, "--paths", "a.py", "b.py", *self.FAIL)
        self.assertEqual(body(cwd, "a.py"), "original\n")
        self.assertEqual(body(cwd, "b.py"), "original\n")

    def test_undeclared_work_is_never_touched(self) -> None:
        """The data-loss guarantee: only declared paths may move."""
        cwd = repo()
        with open(os.path.join(cwd, "precious.txt"), "w", encoding="utf-8") as handle:
            handle.write("unrelated uncommitted work\n")
        loop(cwd, "--paths", "a.py", *self.FAIL)
        self.assertEqual(body(cwd, "precious.txt"), "unrelated uncommitted work\n")
        self.assertEqual(body(cwd, "b.py"), "changed\n")

    def test_no_paths_on_failure_leaves_the_tree_alone(self) -> None:
        cwd = repo()
        result = loop(cwd, *self.FAIL)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(body(cwd, "a.py"), "changed\n")

    def test_auto_commit_without_paths_refuses(self) -> None:
        """It must not fall back to `git add .`, which once swept in unrelated work."""
        cwd = repo()
        result = loop(cwd, "--auto-commit", *self.OK)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--paths", result.stderr)

    def test_a_non_git_target_is_refused(self) -> None:
        tmp = tempfile.mkdtemp()
        self.assertEqual(loop(tmp, "--paths", "a.py", *self.OK).returncode, 66)


class ToolkitConsistencyTests(unittest.TestCase):
    def test_every_paths_flag_accepts_several_values(self) -> None:
        """The root cause was one tool disagreeing with its three siblings about one flag."""
        import re
        for name in ("scripts/callers.py", "scripts/comments.py", "scripts/ruler.py",
                     "autoevolve.py"):
            with open(os.path.join(ROOT, name), encoding="utf-8") as handle:
                source = handle.read()
            match = re.search(r'add_argument\(\s*"--paths",\s*(?:nargs="[+*]")', source)
            self.assertIsNotNone(match, f"{name}: --paths must take several values")


if __name__ == "__main__":
    unittest.main()
