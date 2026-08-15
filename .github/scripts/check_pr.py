#!/usr/bin/env python3
"""AutoEvolve PR Guardrail Checker for GitHub Actions.

Validates pull requests created with AI coding assistants:
1. Diff Size Gate: Checks additions against brevity thresholds.
2. Test File Integrity: Tracks deleted test files and modified test assertions.
3. Direct Code Hygiene: Flags dead commented-out code and narration noise.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import List, Tuple

# Reconfigure stdout/stderr for Unicode safety across Windows and Linux
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MAX_ADDED_LINES = int(os.environ.get("MAX_ADDED_LINES", "200"))
ALLOW_TEST_DELETIONS = os.environ.get("ALLOW_TEST_DELETIONS", "0").lower() in ("1", "true")

ASSERTION_PATTERNS = (
    "assert ",
    "assert(",
    "assert.equal",
    "assert.Equal",
    "assert.strictEqual",
    "assert.deepEqual",
    "expect(",
    "assertEquals",
    "should.",
    "self.assert",
    "self.assertEqual",
    "t.Error",
    "t.Fatal",
)


def run_git(cmd: list[str]) -> str:
    """Execute a git command in a subprocess and return stripped stdout."""
    res = subprocess.run(
        ["git", *cmd],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return res.stdout.strip() if res.stdout else ""


def check_diff_size(base_ref: str) -> Tuple[bool, int, int, str]:
    """Calculate total line additions and deletions in the PR compared to the base branch.

    Args:
        base_ref: The target base branch name (e.g. 'main').

    Returns:
        A tuple of (passed, added_lines_count, deleted_lines_count, status_message).
    """
    stat = run_git(["diff", f"origin/{base_ref}...HEAD", "--shortstat"])
    added = 0
    deleted = 0

    if stat:
        match_add = re.search(r"(\d+) insertion", stat)
        match_del = re.search(r"(\d+) deletion", stat)
        if match_add:
            added = int(match_add.group(1))
        if match_del:
            deleted = int(match_del.group(1))

    passed = (added <= MAX_ADDED_LINES)
    msg = f"Additions: +{added} lines, Deletions: -{deleted} lines (Limit: +{MAX_ADDED_LINES})"
    return passed, added, deleted, msg


def check_test_integrity(base_ref: str) -> Tuple[bool, List[str], List[str]]:
    """Detect deleted test files (hard failure) and removed test assertions (advisory warning).

    Args:
        base_ref: The target base branch name (e.g. 'main').

    Returns:
        A tuple of (passed, hard_violations, advisory_warnings).
    """
    hard_violations: List[str] = []
    advisory_warnings: List[str] = []
    diff_output = run_git(["diff", f"origin/{base_ref}...HEAD"])

    current_file = None
    test_file_pattern = re.compile(
        r"(tests?/.*|test_.*\.py|.*_test\.(py|go|js|ts)|.*\.spec\.(js|ts))",
        re.IGNORECASE,
    )

    for line in diff_output.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            current_file = parts[2].lstrip("a/") if len(parts) >= 3 else None
        elif current_file and test_file_pattern.search(current_file):
            if line.startswith("deleted file mode"):
                if not ALLOW_TEST_DELETIONS:
                    hard_violations.append(f"Deleted test file: `{current_file}`")
                else:
                    advisory_warnings.append(f"Deleted test file (explicitly allowed): `{current_file}`")
            elif line.startswith("-") and not line.startswith("---"):
                removed_code = line[1:].strip()
                if any(x in removed_code for x in ASSERTION_PATTERNS):
                    advisory_warnings.append(
                        f"Modified assertion in `{current_file}`: `{removed_code[:60]}`"
                    )

    passed = (len(hard_violations) == 0)
    return passed, hard_violations, advisory_warnings


def check_direct_code(base_ref: str) -> Tuple[bool, List[str]]:
    """Detect change narration comments (e.g. '# Fix: ...') in newly added code lines.

    Args:
        base_ref: The target base branch name (e.g. 'main').

    Returns:
        A tuple of (passed, list_of_violations).
    """
    violations: List[str] = []
    diff_output = run_git(["diff", f"origin/{base_ref}...HEAD"])

    narration_pattern = re.compile(
        r"^\+\s*#\s*(fix|fixed|update|updated|added|removed|modified|refactored|changed)\s*:",
        re.IGNORECASE,
    )

    current_file = None
    for line in diff_output.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            current_file = parts[3].lstrip("b/") if len(parts) >= 4 else None
        elif line.startswith("+") and not line.startswith("+++"):
            if narration_pattern.search(line):
                violations.append(f"Narration comment in `{current_file}`: `{line[1:].strip()}`")

    passed = (len(violations) == 0)
    return passed, violations


def main() -> int:
    """Entry point for the pull request guardrail validator."""
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")
    print("=== AutoEvolve AI Guardrail PR Check ===")
    print(f"Comparing HEAD against origin/{base_ref}")
    print("-" * 50)

    # 1. Diff Size Check
    size_passed, added, deleted, size_msg = check_diff_size(base_ref)
    size_status = "PASS" if size_passed else "WARN"
    print(f"[{size_status}] Diff Size Gate: {size_msg}")

    # 2. Test Integrity Check
    test_passed, hard_violations, advisory_warnings = check_test_integrity(base_ref)
    test_status = "PASS" if test_passed else "FAIL"
    print(f"[{test_status}] Test Integrity Gate: {len(hard_violations)} deleted test files, {len(advisory_warnings)} modified assertions")
    for hv in hard_violations:
        print(f"       - [BLOCKER] {hv}")
    for aw in advisory_warnings:
        print(f"       - [ADVISORY] {aw}")

    # 3. Direct Code Check
    code_passed, code_violations = check_direct_code(base_ref)
    code_status = "PASS" if code_passed else "WARN"
    print(f"[{code_status}] Direct Code Hygiene: {len(code_violations)} narration comment findings")
    for v in code_violations:
        print(f"       - {v}")

    print("-" * 50)

    # Generate GitHub Step Summary if running in Actions
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("# AutoEvolve AI Guardrail Report\n\n")
            f.write("| Gate | Status | Details |\n|:---|:---:|:---|\n")
            f.write(f"| **Diff Size** | {'✅ Pass' if size_passed else '⚠️ Exceeds Limit'} | +{added} / -{deleted} lines (Max: +{MAX_ADDED_LINES}) |\n")
            f.write(f"| **Test Protection** | {'✅ Intact' if test_passed else '❌ File Deleted'} | {len(hard_violations)} deleted files, {len(advisory_warnings)} modified assertions |\n")
            f.write(f"| **Direct Code** | {'✅ Clean' if code_passed else '⚠️ Narration Found'} | {len(code_violations)} narration findings |\n\n")
            if hard_violations:
                f.write("### ❌ Test File Deletion Blockers\n")
                for hv in hard_violations:
                    f.write(f"- {hv}\n")
            if advisory_warnings:
                f.write("### ℹ️ Modified Test Assertions (Advisory)\n")
                for aw in advisory_warnings:
                    f.write(f"- {aw}\n")

    if not test_passed:
        print("[FAIL] Test integrity check failed. Test files must not be deleted.")
        return 1

    print("[PASS] All required AutoEvolve PR guardrails passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
