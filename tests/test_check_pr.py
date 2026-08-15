"""Unit and integration tests for PR Guardrail checker (check_pr.py)."""
from __future__ import annotations

import importlib.util
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHECK_PR_PATH = os.path.join(REPO_ROOT, ".github", "scripts", "check_pr.py")

spec = importlib.util.spec_from_file_location("check_pr", CHECK_PR_PATH)
assert spec and spec.loader, "Failed to load check_pr module spec"
check_pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_pr)

ASSERTION_PATTERNS = check_pr.ASSERTION_PATTERNS
check_diff_size = check_pr.check_diff_size
check_test_integrity = check_pr.check_test_integrity
check_direct_code = check_pr.check_direct_code


class TestAssertionPatterns:
    def test_assertion_patterns_cover_major_frameworks(self):
        # Python
        assert "assert " in ASSERTION_PATTERNS
        assert "self.assertEqual" in ASSERTION_PATTERNS
        # Jest / Mocha / Chai
        assert "expect(" in ASSERTION_PATTERNS
        assert "should." in ASSERTION_PATTERNS
        # Node assert
        assert "assert.equal" in ASSERTION_PATTERNS
        assert "assert.strictEqual" in ASSERTION_PATTERNS
        # Go
        assert "t.Error" in ASSERTION_PATTERNS
        assert "t.Fatal" in ASSERTION_PATTERNS


class TestNarrationCommentDetection:
    """Test regex pattern matching for change narration comments."""

    @pytest.mark.parametrize(
        "clean_comment",
        [
            "# Note: timeout is in seconds",
            "# TODO: refactor database connection pooling",
            "# type: ignore",
            "# noqa: E501",
            "# See RFC 7231 section 6.5.4 for status codes",
            "# Algorithms require O(N log N) sorting step",
        ],
    )
    def test_clean_comments_are_not_flagged(self, clean_comment, monkeypatch):
        diff_text = f"diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n+{clean_comment}\n"
        monkeypatch.setattr(check_pr, "run_git", lambda cmd: diff_text)

        passed, violations = check_direct_code("main")
        assert passed is True
        assert len(violations) == 0

    @pytest.mark.parametrize(
        "narration_comment",
        [
            "# Fix: updated the timeout value",
            "# Fixed: resolved off-by-one bug in loop",
            "# Update: changed return type to bytes",
            "# Added: new helper function for validation",
            "# Removed: deleted deprecated class",
            "# Modified: restructured error handling logic",
            "# Refactored: extracted common logic into util",
            "# Changed: adjusted default retry count",
        ],
    )
    def test_narration_comments_are_flagged(self, narration_comment, monkeypatch):
        diff_text = f"diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n+{narration_comment}\n"
        monkeypatch.setattr(check_pr, "run_git", lambda cmd: diff_text)

        passed, violations = check_direct_code("main")
        assert passed is False
        assert len(violations) >= 1
        assert "Narration comment in `app.py`" in violations[0]


class TestDiffSizeGate:
    def test_diff_under_limit_passes(self, monkeypatch):
        monkeypatch.setattr(
            check_pr,
            "run_git",
            lambda cmd: " 2 files changed, 45 insertions(+), 10 deletions(-)",
        )
        passed, added, deleted, msg = check_diff_size("main")
        assert passed is True
        assert added == 45
        assert deleted == 10

    def test_diff_over_limit_warns(self, monkeypatch):
        monkeypatch.setattr(
            check_pr,
            "run_git",
            lambda cmd: " 10 files changed, 450 insertions(+), 20 deletions(-)",
        )
        passed, added, deleted, msg = check_diff_size("main")
        assert passed is False
        assert added == 450


class TestTestIntegrityGate:
    def test_deleted_test_file_is_hard_blocker(self, monkeypatch):
        diff_text = "diff --git a/tests/test_billing.py b/tests/test_billing.py\ndeleted file mode 100644\n--- a/tests/test_billing.py\n+++ /dev/null\n@@ -1,5 +0,0 @@\n-def test_billing():\n-    assert True\n"
        monkeypatch.setattr(check_pr, "run_git", lambda cmd: diff_text)

        passed, hard_violations, advisory_warnings = check_test_integrity("main")
        assert passed is False
        assert len(hard_violations) == 1
        assert "Deleted test file: `tests/test_billing.py`" in hard_violations[0]

    def test_modified_assertion_is_advisory_warning_not_hard_blocker(self, monkeypatch):
        diff_text = "diff --git a/tests/test_auth.py b/tests/test_auth.py\n--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n@@ -5,1 +5,1 @@\n-    assert user.is_valid() == True\n+    assert user.is_authenticated() is True\n"
        monkeypatch.setattr(check_pr, "run_git", lambda cmd: diff_text)

        passed, hard_violations, advisory_warnings = check_test_integrity("main")
        assert passed is True
        assert len(hard_violations) == 0
        assert len(advisory_warnings) == 1
        assert "Modified assertion in `tests/test_auth.py`" in advisory_warnings[0]
