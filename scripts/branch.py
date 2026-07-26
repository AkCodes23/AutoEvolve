#!/usr/bin/env python3
"""Population Branch Manager for AutoEvolve deep mode.

Helps agents maintain quality-diversity niche candidate branches (e.g. evolve/fast, evolve/small).
Usage:
    python scripts/branch.py create <niche_name>
    python scripts/branch.py list
    python scripts/branch.py clean
"""
import os
import subprocess
import sys


def run_git(args: list[str]) -> tuple[int, str]:
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    out = (res.stdout + "\n" + res.stderr).strip()
    return res.returncode, out


def cmd_create(name: str) -> int:
    branch_name = f"evolve/{name}" if not name.startswith("evolve/") else name
    code, out = run_git(["checkout", "-b", branch_name])
    if code == 0:
        print(f"[branch] Created and checked out niche branch '{branch_name}'")
    else:
        if "not a git repository" in out.lower():
            print("[branch] Target repository is not a git repo. Run 'git init' first.", file=sys.stderr)
        else:
            print(f"[branch] Failed to create branch '{branch_name}': {out}", file=sys.stderr)
    return code


def cmd_list() -> int:
    code, out = run_git(["branch", "--list", "evolve/*"])
    if code != 0:
        if "not a git repository" in out.lower():
            print("[branch] Target repository is not a git repo. Run 'git init' first.")
            return 0
        print(f"[branch] Failed to list branches: {out}", file=sys.stderr)
        return code
    if not out:
        print("[branch] No active niche population branches (evolve/*).")
    else:
        print("[branch] Active niche population branches:")
        for line in out.splitlines():
            print(f"  {line}")
    return 0


def get_primary_branch() -> str:
    # Check if main exists, then master, else fallback to current branch
    code_main, _ = run_git(["rev-parse", "--verify", "main"])
    if code_main == 0:
        return "main"
    code_master, _ = run_git(["rev-parse", "--verify", "master"])
    if code_master == 0:
        return "master"
    code_head, out_head = run_git(["branch", "--show-current"])
    return out_head.strip() if code_head == 0 and out_head.strip() else "main"


def cmd_clean() -> int:
    code, out = run_git(["branch", "--list", "evolve/*"])
    if code != 0:
        if "not a git repository" in out.lower():
            print("[branch] Target repository is not a git repo. Run 'git init' first.")
            return 0
        print(f"[branch] Failed to list branches: {out}", file=sys.stderr)
        return code
    if not out:
        print("[branch] No niche branches to clean.")
        return 0
    branches = [b.strip().replace("* ", "") for b in out.splitlines()]
    print(f"[branch] Cleaning {len(branches)} niche branches...")
    target_branch = get_primary_branch()
    run_git(["checkout", target_branch])
    for b in branches:
        c, o = run_git(["branch", "-D", b])
        print(f"  Deleted {b}: {'ok' if c == 0 else o}")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/branch.py [create <name> | list | clean]")
        return 64
    subcmd = sys.argv[1].lower()
    if subcmd == "create" and len(sys.argv) >= 3:
        return cmd_create(sys.argv[2])
    elif subcmd == "list":
        return cmd_list()
    elif subcmd == "clean":
        return cmd_clean()
    else:
        print("Usage: python scripts/branch.py [create <name> | list | clean]")
        return 64


if __name__ == "__main__":
    sys.exit(main())
