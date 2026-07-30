"""Calibration tests for the frozen-signal reporter.

Same discipline as the other two: every detector is pinned on a change it must flag and on a
change it must not. The must-not half matters more here than anywhere else in this repository,
because this tool accuses, and people legitimately edit tests all day. The false-positive cases
below are real commits from `pallets/click` and `urllib3/urllib3`.
"""
from __future__ import annotations

import os
import sys
import textwrap
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ruler  # noqa: E402

BEFORE = '''
    import pytest

    def test_add():
        assert add(1, 2) == 3
        assert add(0, 0) == 0

    def test_sub():
        assert sub(5, 3) == 2

    class TestDiv:
        def test_exact(self):
            assert div(6, 3) == 2
'''


def diff(after: str, before: str = BEFORE, **kw) -> list[tuple[str, str, str]]:
    return ruler.compare(textwrap.dedent(before), textwrap.dedent(after), **kw)


def tiers(after: str, before: str = BEFORE, **kw) -> list[str]:
    return [tier for tier, _, _ in diff(after, before, **kw)]


class WeakenedTests(unittest.TestCase):
    def test_a_deleted_test_is_flagged(self) -> None:
        after = BEFORE.replace("def test_sub():\n        assert sub(5, 3) == 2\n", "")
        self.assertIn("weakened", tiers(after))

    def test_a_newly_skipped_test_is_flagged(self) -> None:
        after = BEFORE.replace("def test_sub():", "@pytest.mark.skip\n    def test_sub():")
        found = [m for t, _, m in diff(after) if t == "weakened"]
        self.assertTrue(any("skip" in m for m in found), found)

    def test_a_method_inside_a_class_is_tracked(self) -> None:
        after = BEFORE.replace("        def test_exact(self):\n            assert div(6, 3) == 2\n", "")
        self.assertIn("weakened", tiers(after))


class NotWeakenedTests(unittest.TestCase):
    def test_adding_a_test_is_not_a_finding(self) -> None:
        self.assertEqual(tiers(BEFORE + "\n    def test_mul():\n        assert mul(2, 3) == 6\n"), [])

    def test_an_unchanged_file_is_not_a_finding(self) -> None:
        self.assertEqual(tiers(BEFORE), [])

    def test_a_rename_keeping_the_body_is_not_a_deletion(self) -> None:
        self.assertEqual(tiers(BEFORE.replace("def test_sub():", "def test_subtract():")), [])

    def test_a_test_moved_to_another_file_is_not_a_deletion(self) -> None:
        """pallets/click 7007982 split tests/test_utils.py into a directory.

        Judged per file it read as ten deleted tests, which is a tidy-up reported as the worst
        thing this tool can say. The names and bodies present anywhere in the ruler after the
        change are what distinguish a move from a removal.
        """
        after = BEFORE.replace("def test_sub():\n        assert sub(5, 3) == 2\n", "")
        self.assertIn("weakened", tiers(after))
        self.assertEqual(tiers(after, elsewhere_names=frozenset({"test_sub"})), [])

    def test_a_strengthened_test_is_not_a_finding(self) -> None:
        after = BEFORE.replace("assert sub(5, 3) == 2",
                               "assert sub(5, 3) == 2\n        assert sub(0, 1) == -1")
        self.assertEqual(tiers(after), [])


class ReviewTests(unittest.TestCase):
    def test_losing_an_assertion_is_review_not_weakened(self) -> None:
        after = BEFORE.replace("        assert add(0, 0) == 0\n", "")
        self.assertEqual(tiers(after), ["review"])

    def test_a_changed_expectation_is_review(self) -> None:
        after = BEFORE.replace("assert sub(5, 3) == 2", "assert sub(5, 3) == 99")
        self.assertEqual(tiers(after), ["review"])

    def test_unittest_style_assertions_are_counted(self) -> None:
        before = '''
            class TestThing:
                def test_it(self):
                    self.assertEqual(add(1, 2), 3)
                    self.assertTrue(ok())
        '''
        after = '''
            class TestThing:
                def test_it(self):
                    self.assertEqual(add(1, 2), 3)
        '''
        self.assertEqual(tiers(after, before), ["review"])


class ScopeTests(unittest.TestCase):
    def test_direction_md_signal_beats_convention(self) -> None:
        self.assertTrue(ruler.is_ruler("suite/check_all.py", ["suite"]))
        self.assertFalse(ruler.is_ruler("tests/test_x.py", ["suite"]))

    def test_convention_is_the_fallback(self) -> None:
        for rel in ["tests/test_x.py", "test_x.py", "x_test.py", "conftest.py", "a/tests/b.py"]:
            self.assertTrue(ruler.is_ruler(rel, []), rel)
        for rel in ["src/app.py", "docs/testing.md", "src/latest.py"]:
            self.assertFalse(ruler.is_ruler(rel, []), rel)

    def test_an_unfilled_placeholder_names_nothing(self) -> None:
        """cmd_setup leaves `{{TEST_SIGNAL}}` when it cannot detect a runner."""
        import tempfile
        for signal in ["{{TEST_SIGNAL}}", "<how better is judged>"]:
            tmp = tempfile.mkdtemp()
            with open(os.path.join(tmp, "DIRECTION.md"), "w", encoding="utf-8") as handle:
                handle.write(f"# DIRECTION\n\nSignal:     {signal} (how better is judged)\n")
            self.assertEqual(ruler.signal_paths(tmp), [], signal)

    def test_a_real_signal_line_yields_its_path(self) -> None:
        import tempfile
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "DIRECTION.md"), "w", encoding="utf-8") as handle:
            handle.write("# DIRECTION\n\nSignal:     pytest tests/ (how better is judged)\n")
        self.assertEqual(ruler.signal_paths(tmp), ["tests"])


class UnreadableRulerTests(unittest.TestCase):
    """A ruler file this tool cannot parse must never be reported as an unchanged signal.

    Before this, a TypeScript repo that deleted half its suite got "No changes to the frozen
    signal" and exit 0, because the changed-file list was filtered to Python before anything
    asked whether those files were part of the ruler. A silent pass is the one failure this
    tool exists to prevent, so it is the one failure it must not commit itself.
    """

    def _repo(self, files: dict[str, str]) -> str:
        import subprocess
        import tempfile
        root = tempfile.mkdtemp()
        run = lambda *a: subprocess.run(["git", "-C", root, *a], capture_output=True)
        run("init")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        for rel, body in files.items():
            full = os.path.join(root, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as handle:
                handle.write(body)
        run("add", "-A")
        run("commit", "-m", "init")
        return root

    def _run(self, root: str) -> str:
        import io
        import contextlib
        argv = sys.argv
        sys.argv = ["ruler.py", "--root", root]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                ruler.main()
        finally:
            sys.argv = argv
        return out.getvalue()

    def test_a_deleted_javascript_test_is_not_an_all_clear(self) -> None:
        root = self._repo({"tests/auth.test.ts": "test('a', () => {});\ntest('b', () => {});\n"})
        with open(os.path.join(root, "tests", "auth.test.ts"), "w", encoding="utf-8") as handle:
            handle.write("test('a', () => {});\n")
        text = self._run(root)
        self.assertNotIn("No changes to the frozen signal", text)
        self.assertIn("auth.test.ts", text)

    def test_a_mixed_change_does_not_let_the_tally_cover_unread_files(self) -> None:
        root = self._repo({
            "tests/auth.test.ts": "test('a', () => {});\ntest('b', () => {});\n",
            "tests/test_core.py": "def test_x():\n    assert compute(1) == 2\n"
                                  "def test_y():\n    assert other() == 5\n",
        })
        for rel, body in (("tests/auth.test.ts", "test('a', () => {});\n"),
                          ("tests/test_core.py", "def test_x():\n    assert compute(1) == 2\n")):
            with open(os.path.join(root, rel), "w", encoding="utf-8") as handle:
                handle.write(body)
        text = self._run(root)
        self.assertIn("test_y", text)                       # the Python finding still lands
        self.assertIn("auth.test.ts", text)                 # and the unread file is named
        self.assertIn("across the Python files only", text)

    def test_a_python_only_repo_still_says_no_changes(self) -> None:
        root = self._repo({"tests/test_core.py": "def test_x():\n    assert compute(1) == 2\n",
                           "src/app.py": "def compute(n):\n    return n + 1\n"})
        with open(os.path.join(root, "src", "app.py"), "w", encoding="utf-8") as handle:
            handle.write("def compute(n):\n    return n + 2\n")
        self.assertIn("No changes to the frozen signal", self._run(root))

    def test_changed_files_can_return_every_language(self) -> None:
        from callers import changed_files
        root = self._repo({"a.py": "x = 1\n", "b.ts": "const x = 1;\n"})
        with open(os.path.join(root, "b.ts"), "w", encoding="utf-8") as handle:
            handle.write("const x = 2;\n")
        self.assertEqual(changed_files(root, None), [])
        self.assertEqual(changed_files(root, None, suffix=None), ["b.ts"])


class NoGateTests(unittest.TestCase):
    def test_the_tool_has_no_strict_mode(self) -> None:
        """Deliberate. Nothing here is provable, so a gate would block honest work.

        If someone adds --strict later, this fails and they have to argue for it in a place a
        reviewer will read, rather than discovering it when a commit is refused.
        """
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ruler.py"),
                  encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("--strict", source.split('"""', 2)[2])


if __name__ == "__main__":
    unittest.main()
