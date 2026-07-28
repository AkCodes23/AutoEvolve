#!/usr/bin/env python3
"""Population Branch Manager for AutoEvolve deep mode.

Maintains the quality-diversity niche branches (evolve/fast, evolve/small, ...) that hold
non-champion candidates while HEAD holds the champion.

Usage:
    python scripts/branch.py create <niche_name> [--target DIR]
    python scripts/branch.py list [--target DIR]
    python scripts/branch.py clean [--target DIR] [--dry-run] [--force]

`clean` deletes branches, so it defaults to `git branch -d`, which refuses to drop unmerged
work. An earlier version used `git branch -D` unconditionally, discarded the return code of the
checkout that precedes it, and returned 0 even when it had partially destroyed the candidate
population on a dirty tree. Those branches are the experiment record: the README calls them
"real branches you can evolve from", and AGENTS.md requires pausing for a human before anything
hard to reverse.
"""
import argparse
import os
import sys


def run_git(args: list[str], cwd: str) -> tuple[int, str]:
    import subprocess
    res = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return res.returncode, (res.stdout + "\n" + res.stderr).strip()


def _require_repo(cwd: str) -> bool:
    code, _ = run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    if code != 0:
        print(f"[branch] '{cwd}' is not a git work tree. Run 'git init' first.", file=sys.stderr)
        return False
    return True


def _niche_branches(cwd: str) -> tuple[int, list[str]]:
    code, out = run_git(["branch", "--list", "evolve/*"], cwd)
    if code != 0:
        print(f"[branch] Failed to list branches: {out}", file=sys.stderr)
        return code, []
    return 0, [b.strip().lstrip("* ").strip() for b in out.splitlines() if b.strip()]


def cmd_create(name: str, cwd: str) -> int:
    if not _require_repo(cwd):
        return 66
    branch_name = name if name.startswith("evolve/") else f"evolve/{name}"
    code, out = run_git(["checkout", "-b", branch_name], cwd)
    if code == 0:
        print(f"[branch] Created and checked out niche branch '{branch_name}'")
    else:
        print(f"[branch] Failed to create branch '{branch_name}': {out}", file=sys.stderr)
    return code


def cmd_list(cwd: str) -> int:
    if not _require_repo(cwd):
        return 66
    code, branches = _niche_branches(cwd)
    if code != 0:
        return code
    if not branches:
        print("[branch] No active niche population branches (evolve/*).")
        return 0
    print("[branch] Active niche population branches:")
    for branch in branches:
        unmerged, _ = _unmerged_count(branch, cwd)
        note = f"{unmerged} commit(s) not in HEAD" if unmerged else "fully merged into HEAD"
        print(f"  {branch}  ({note})")
    return 0


def _unmerged_count(branch: str, cwd: str) -> tuple[int, str]:
    """How many commits exist on `branch` that HEAD does not already contain."""
    code, out = run_git(["rev-list", "--count", f"HEAD..{branch}"], cwd)
    if code != 0:
        return 0, out
    try:
        return int(out.splitlines()[0].strip()), ""
    except (ValueError, IndexError):
        return 0, out


def get_primary_branch(cwd: str) -> str:
    for candidate in ("main", "master"):
        code, _ = run_git(["rev-parse", "--verify", candidate], cwd)
        if code == 0:
            return candidate
    code, out = run_git(["branch", "--show-current"], cwd)
    return out.strip() if code == 0 and out.strip() else "main"


def cmd_clean(cwd: str, dry_run: bool = False, force: bool = False) -> int:
    if not _require_repo(cwd):
        return 66
    code, branches = _niche_branches(cwd)
    if code != 0:
        return code
    if not branches:
        print("[branch] No niche branches to clean.")
        return 0

    print(f"[branch] {len(branches)} niche branch(es) considered:")
    for branch in branches:
        unmerged, _ = _unmerged_count(branch, cwd)
        fate = "would delete" if not unmerged else ("would FORCE-delete" if force else "would KEEP (unmerged)")
        print(f"  {branch}: {unmerged} commit(s) not in HEAD -> {fate}")
    if dry_run:
        print("[branch] --dry-run: nothing deleted.")
        return 0

    target_branch = get_primary_branch(cwd)
    code, out = run_git(["checkout", target_branch], cwd)
    if code != 0:
        # Deleting the branch we are standing on fails, and on a dirty tree the checkout itself
        # fails. Continuing from here is how the population got partially destroyed before.
        print(f"[branch] Refusing to clean: could not switch to '{target_branch}': {out}",
              file=sys.stderr)
        return code

    failed = 0
    for branch in branches:
        flag = "-D" if force else "-d"
        code, out = run_git(["branch", flag, branch], cwd)
        if code == 0:
            print(f"  Deleted {branch}")
        else:
            failed += 1
            print(f"  Kept {branch}: {out}", file=sys.stderr)
    if failed:
        print(f"[branch] {failed} branch(es) not deleted. They hold work not in HEAD; review "
              "them, then re-run with --force to discard.", file=sys.stderr)
    return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subcommand", choices=["create", "list", "clean"])
    parser.add_argument("name", nargs="?", help="niche name, for `create`")
    parser.add_argument("--target", default=os.getcwd(),
                        help="repository to act on (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="`clean`: show what would happen")
    parser.add_argument("--force", action="store_true",
                        help="`clean`: discard branches holding commits not in HEAD")
    args = parser.parse_args()

    cwd = os.path.abspath(args.target)
    if not os.path.isdir(cwd):
        print(f"[branch] Target '{cwd}' is not a directory.", file=sys.stderr)
        return 66
    if args.subcommand == "create":
        if not args.name:
            parser.error("create needs a niche name")
        return cmd_create(args.name, cwd)
    if args.subcommand == "list":
        return cmd_list(cwd)
    return cmd_clean(cwd, args.dry_run, args.force)


if __name__ == "__main__":
    sys.exit(main())
