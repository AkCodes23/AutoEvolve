#!/usr/bin/env python3
"""AutoEvolve PR Guardrail Checker for GitHub Actions.

Validates pull requests created with AI coding assistants:
1. Diff Size Gate (YAGNI & brevity)
2. Test File Integrity (Prevents test tampering / silent test deletion)
3. Direct Code Hygiene (Flags dead commented-out code and narration noise)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys


MAX_ADDED_LINES = int(os.environ.get("MAX_ADDED_LINES", "200"))


def run_git(cmd: list[str]) -> str:
    res = subprocess.run(["git", *cmd], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def check_diff_size(base_ref: str) -> tuple[bool, int, int, str]:
    """Calculate additions and deletions against base branch."""
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


def check_test_integrity(base_ref: str) -> tuple[bool, list[str]]:
    """Detect deleted test files or removed test assertions."""
    violations = []
    diff_output = run_git(["diff", f"origin/{base_ref}...HEAD"])

    current_file = None
    test_file_pattern = re.compile(r"(tests?/.*|test_.*\.py|.*_test\.(py|go|js|ts)|.*\.spec\.(js|ts))", re.IGNORECASE)

    for line in diff_output.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            current_file = parts[2].lstrip("a/") if len(parts) >= 3 else None
        elif current_file and test_file_pattern.search(current_file):
            if line.startswith("deleted file mode"):
                violations.append(f"Deleted test file: `{current_file}`")
            elif line.startswith("-") and not line.startswith("---"):
                # Removed lines in test files
                removed_code = line[1:].strip()
                if any(x in removed_code for x in ("assert ", "expect(", "assertEquals", "should.", "self.assert")):
                    violations.append(f"Removed test assertion in `{current_file}`: `{removed_code[:60]}`")

    passed = (len(violations) == 0)
    return passed, violations


def check_direct_code(base_ref: str) -> tuple[bool, list[str]]:
    """Detect dead commented-out code or change narration in modified lines."""
    violations = []
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
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")
    print(f"=== AutoEvolve AI Guardrail PR Check ===")
    print(f"Comparing HEAD against origin/{base_ref}")
    print("-" * 50)

    # 1. Diff Size Check
    size_passed, added, deleted, size_msg = check_diff_size(base_ref)
    size_status = "PASS" if size_passed else "WARN"
    print(f"[{size_status}] Diff Size Gate: {size_msg}")

    # 2. Test Integrity Check
    test_passed, test_violations = check_test_integrity(base_ref)
    test_status = "PASS" if test_passed else "FAIL"
    print(f"[{test_status}] Test Integrity Gate: {len(test_violations)} potential test weakening findings")
    for v in test_violations:
        print(f"       - {v}")

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
            f.write(f"| Gate | Status | Details |\n|:---|:---:|:---|\n")
            f.write(f"| **Diff Size** | {'✅ Pass' if size_passed else '⚠️ Exceeds Limit'} | +{added} / -{deleted} lines (Max: +{MAX_ADDED_LINES}) |\n")
            f.write(f"| **Test Protection** | {'✅ Intact' if test_passed else '❌ Weakened'} | {len(test_violations)} removed assertions |\n")
            f.write(f"| **Direct Code** | {'✅ Clean' if code_passed else '⚠️ Narration Found'} | {len(code_violations)} narration findings |\n\n")
            if test_violations:
                f.write("### ⚠️ Test Weakening Findings\n")
                for v in test_violations:
                    f.write(f"- {v}\n")

    # Fail PR only if test assertions were tampered with
    if not test_passed:
        print("❌ Test integrity check failed. Never optimize the scorer.")
        return 1

    print("✅ All required AutoEvolve PR guardrails passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
