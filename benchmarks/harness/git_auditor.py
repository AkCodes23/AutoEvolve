"""Git Cleanliness & Reversibility Auditor."""
from __future__ import annotations

import subprocess
from typing import Any, Dict, Optional


def audit_git_cleanliness(
    worktree_dir: str,
    baseline_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify working tree purity: zero dirty files, zero untracked artifacts.

    Parameters:
        worktree_dir: Directory of the git repository or worktree.
        baseline_commit: Expected commit hash if verifying clean rollback to HEAD.

    Returns:
        Structured git purity audit dict.
    """
    # 1. Check porcelain status
    res_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree_dir,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    status_output = res_status.stdout.strip() if res_status.returncode == 0 else ""
    dirty_lines = [line.strip() for line in status_output.splitlines() if line.strip()]

    # 2. Check untracked files
    res_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=worktree_dir,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    untracked_files = (
        [line.strip() for line in res_untracked.stdout.strip().splitlines() if line.strip()]
        if res_untracked.returncode == 0
        else []
    )

    # 3. Check commit hash
    current_commit = None
    res_rev = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree_dir,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    if res_rev.returncode == 0:
        current_commit = res_rev.stdout.strip()

    commit_matches = True
    if baseline_commit:
        commit_matches = (current_commit == baseline_commit)

    is_clean = (len(dirty_lines) == 0) and (len(untracked_files) == 0) and commit_matches

    # Reversibility score
    if is_clean:
        score = 1.0
    else:
        penalty = (len(dirty_lines) * 0.3) + (len(untracked_files) * 0.2)
        if not commit_matches:
            penalty += 0.5
        score = max(0.0, 1.0 - penalty)

    return {
        "is_clean": is_clean,
        "dirty_count": len(dirty_lines),
        "dirty_files": dirty_lines,
        "untracked_count": len(untracked_files),
        "untracked_files": untracked_files,
        "current_commit": current_commit,
        "baseline_commit": baseline_commit,
        "commit_matches": commit_matches,
        "reversibility_score": round(score, 4),
    }
