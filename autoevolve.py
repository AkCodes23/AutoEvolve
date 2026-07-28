#!/usr/bin/env python3
"""AutoEvolve Universal Cross-Platform CLI Tool.

Enables installation, template initialization, and readiness checking of the AutoEvolve
mindset in ANY target repository across Windows, macOS, and Linux.

Usage:
    python autoevolve.py install --target /path/to/project [--dry-run]
    python autoevolve.py init --target /path/to/project
    python autoevolve.py check --target /path/to/project
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "scripts")
TEMPLATES_DIR = os.path.join(HERE, "templates")


def cmd_install(target: str, dry_run: bool = False) -> int:
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs):
        print(f"Error: Target path '{target_abs}' does not exist.", file=sys.stderr)
        return 66
    elif not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is a file, not a directory.", file=sys.stderr)
        return 66

    print(f"[autoevolve] Installing AutoEvolve into target: {target_abs}")

    # Use native PowerShell script on Windows, or shell script / Python fallback
    if sys.platform == "win32":
        ps_script = os.path.join(HERE, "install.ps1")
        # Resolve the interpreter the same way the POSIX branch does, and prefer PowerShell 7
        # (`pwsh`) where it exists. Hardcoding "powershell" fails on a machine that ships only
        # pwsh, and skipping -NoProfile loaded the user's profile into the installer run.
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if not shell:
            print("Error: neither pwsh nor powershell was found on PATH. Run install.ps1 "
                  "directly, or use install.sh under a POSIX shell.", file=sys.stderr)
            return 69
        cmd = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script,
               "-Target", target_abs]
        if dry_run:
            cmd.append("-DryRun")
        res = subprocess.run(cmd, timeout=120)
        return res.returncode
    else:
        sh_script = os.path.join(HERE, "install.sh")
        bash_bin = shutil.which("bash") or "sh"
        cmd = [bash_bin, sh_script, "--target", target_abs]
        if dry_run:
            cmd.append("--dry-run")
        res = subprocess.run(cmd, timeout=120)
        return res.returncode


def cmd_init(target: str) -> int:
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs):
        print(f"Error: Target path '{target_abs}' does not exist.", file=sys.stderr)
        return 66
    elif not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is a file, not a directory.", file=sys.stderr)
        return 66

    direction_dst = os.path.join(target_abs, "DIRECTION.md")
    journal_dst = os.path.join(target_abs, "JOURNAL.md")

    direction_src = os.path.join(TEMPLATES_DIR, "DIRECTION.md")
    journal_src = os.path.join(TEMPLATES_DIR, "JOURNAL.md")

    count = 0
    if not os.path.exists(direction_dst) and os.path.exists(direction_src):
        shutil.copy(direction_src, direction_dst)
        print(f"  [+] Created {direction_dst}")
        count += 1
    elif os.path.exists(direction_dst):
        print(f"  [-] Skipped DIRECTION.md (already exists)")

    if not os.path.exists(journal_dst) and os.path.exists(journal_src):
        shutil.copy(journal_src, journal_dst)
        print(f"  [+] Created {journal_dst}")
        count += 1
    elif os.path.exists(journal_dst):
        print(f"  [-] Skipped JOURNAL.md (already exists)")

    print(f"[autoevolve] Scaffolding complete ({count} template file(s) created).")
    return 0


def cmd_check(target: str) -> int:
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs):
        print(f"Error: Target path '{target_abs}' does not exist.", file=sys.stderr)
        return 66
    elif not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is a file, not a directory.", file=sys.stderr)
        return 66

    check_script = os.path.join(SCRIPTS_DIR, "check_target.py")
    res = subprocess.run([sys.executable, check_script, "--target", target_abs], timeout=120)
    return res.returncode


def cmd_setup(target: str) -> int:
    """One-command full setup: install AGENTS.md/adapters, scaffold templates, and detect stack."""
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is not a valid directory.", file=sys.stderr)
        return 66

    print(f"[autoevolve] Running one-command setup for target: {target_abs}")
    rc_inst = cmd_install(target_abs)
    rc_init = cmd_init(target_abs)

    # Shared with `check`, deliberately. These were two tables that disagreed: this one counted a
    # bare `tests/` directory as pytest and wrote "pytest tests/" into DIRECTION.md, while the
    # checker did not, so `check` reported "Test Runner: None" for a repo `setup` had just
    # configured. One command contradicting another about the same directory is worse than either
    # answer alone.
    sys.path.insert(0, SCRIPTS_DIR)
    from check_target import detect_signal

    _, detected = detect_signal(target_abs)
    detected = detected or "manual test command"

    # Customize DIRECTION.md if template placeholder exists
    direction_path = os.path.join(target_abs, "DIRECTION.md")
    if os.path.exists(direction_path):
        try:
            with open(direction_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "{{TEST_SIGNAL}}" in content:
                updated = content.replace("{{TEST_SIGNAL}}", detected)
                with open(direction_path, "w", encoding="utf-8") as f:
                    f.write(updated)
                print(f"  [+] Customized DIRECTION.md test signal to: '{detected}'")
        except Exception:
            pass

    if rc_inst == 0 and rc_init == 0:
        print(f"[autoevolve] Setup complete. Suggested test signal for DIRECTION.md: '{detected}'")
        return 0
    # Do not claim success when the install refused. The exit code was already correct here, but
    # the message said "Setup complete!" even when AGENTS.md needed a manual merge and was never
    # written, which is the one case where the user most needs to know nothing is active.
    print(f"[autoevolve] Setup did NOT complete (install exit {rc_inst}, scaffold exit {rc_init}). "
          "Review the messages above: AGENTS.md may still need a manual merge, in which case the "
          "mindset is not yet active in this target.", file=sys.stderr)
    return 1


def cmd_journal(target: str, commit: str, signal: str, action: str, changed: str, why: str) -> int:
    """Append a structured experiment log line to JOURNAL.md."""
    target_abs = os.path.abspath(target)
    journal_path = os.path.join(target_abs, "JOURNAL.md")
    if not os.path.exists(journal_path):
        # Create only the journal. Calling cmd_init here also produced DIRECTION.md, which the
        # docs describe as human-owned: the agent must never author its own objective.
        template = os.path.join(TEMPLATES_DIR, "JOURNAL.md")
        if os.path.exists(template):
            shutil.copy(template, journal_path)
            print(f"  [+] Created {journal_path}")

    entry = f"- {commit} · {signal} · {action.lower()} · {changed} · {why}\n"
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[autoevolve] Journal entry appended to {journal_path}:\n  {entry.strip()}")
    return 0


def cmd_hooks(target: str, force: bool = False) -> int:
    """Install zero-dependency pre-commit hook into target repository."""
    target_abs = os.path.abspath(target)
    hooks_dir = os.path.join(target_abs, ".git", "hooks")
    if not os.path.exists(hooks_dir):
        print(f"Error: Target path '{target_abs}' is not a git repository root (no .git/hooks found).", file=sys.stderr)
        return 66

    hook_path = os.path.join(hooks_dir, "pre-commit")
    if os.path.exists(hook_path) and not force:
        # .git/hooks is not tracked, so an overwrite here is unrecoverable: git cannot restore
        # a hook it never had. Match install.sh's manual-merge exit code rather than exit 0.
        print(f"  [-] Skipped {hook_path} (already exists; not overwriting).\n"
              "      Merge the AutoEvolve checks into your hook manually, or pass --force "
              "(which first writes a .autoevolve-backup copy).", file=sys.stderr)
        return 2
    if os.path.exists(hook_path) and force:
        backup = hook_path + ".autoevolve-backup"
        shutil.copy2(hook_path, backup)
        print(f"  [+] Backed up existing hook to {backup}")
    script_content = (
        "#!/bin/sh\n"
        "# AutoEvolve pre-commit hook: enforces adapter checksum and invariant checks.\n"
        "# Resolve an interpreter rather than hardcoding python3, which frequently does not\n"
        "# exist on Windows and would otherwise block every commit in this repository.\n"
        "PY=\"$(command -v python3 || command -v python)\"\n"
        "if [ -z \"$PY\" ]; then\n"
        "    echo '[autoevolve pre-commit] no python found on PATH; skipping checks' >&2\n"
        "    exit 0\n"
        "fi\n"
        "echo '[autoevolve pre-commit] Running invariant checks...'\n"
        "if [ -f \"scripts/check.py\" ]; then\n"
        "    \"$PY\" scripts/check.py || exit 1\n"
        "fi\n"
        "if [ -f \"scripts/build_adapters.py\" ]; then\n"
        "    \"$PY\" scripts/build_adapters.py --check || exit 1\n"
        "fi\n"
        "# --staged reads the index in Python, so a path containing a space cannot become two\n"
        "# arguments here, and it implies --baseline HEAD, so only noise THIS change introduces\n"
        "# can block a commit. Without that, adopting the hook in an existing repository fails\n"
        "# every commit to a file someone else left a stale comment in, and it gets switched off.\n"
        "# Restatement candidates are printed for you to judge and never fail.\n"
        "if [ -f \"scripts/comments.py\" ]; then\n"
        "    \"$PY\" scripts/comments.py --staged --strict || exit 1\n"
        "fi\n"
        "echo '[autoevolve pre-commit] Checks passed.'\n"
        "exit 0\n"
    )

    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script_content)

    try:
        os.chmod(hook_path, 0o755)
    except Exception:
        pass

    print(f"[autoevolve] Installed pre-commit hook: {hook_path}")
    return 0


def _git(args: list, cwd: str, what: str | None = None):
    """Run git, and never swallow a failure. Returns the CompletedProcess."""
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0 and what:
        print(f"Error: {what} failed (git {' '.join(args)} exited {res.returncode}): "
              f"{res.stderr.strip()}", file=sys.stderr)
    return res


def _revert_paths(target_abs: str, paths: list) -> None:
    """Undo only the declared experiment paths.

    `git checkout HEAD -- <path>` restores from the commit, not from the index, so a change the
    experiment had already staged is genuinely undone. Untracked paths are not in HEAD, so they
    are removed explicitly rather than by any bulk cleanup.
    """
    tracked, untracked = [], []
    for path in paths:
        in_head = _git(["ls-files", "--error-unmatch", "--", path], target_abs).returncode == 0
        (tracked if in_head else untracked).append(path)
    if tracked:
        _git(["checkout", "HEAD", "--", *tracked], target_abs, "revert of tracked paths")
        print(f"  reverted from HEAD: {', '.join(tracked)}")
    for path in untracked:
        full = os.path.join(target_abs, path)
        if os.path.isfile(full):
            os.remove(full)
            print(f"  removed untracked artifact: {path}")
        elif os.path.isdir(full):
            shutil.rmtree(full)
            print(f"  removed untracked directory: {path}")


def cmd_loop(target: str, cmdv: list, message: str | None = None, auto_commit: bool = False,
             paths: list | None = None) -> int:
    """Run the signal, then keep or revert ONLY the declared experiment paths.

    `--paths` is required for any tree-modifying outcome. Nothing here may guess which edits
    belong to the experiment: an earlier version ran `git checkout -- .` on failure and
    `git add .` on success, which permanently destroyed a user's unrelated uncommitted work
    (verified: no reflog entry, no dangling blob, unrecoverable) and swept unrelated files into
    the experiment's commit. AGENTS.md requires reverting created or edited files explicitly,
    with no bulk cleanup, and pausing for a human before anything hard to reverse.
    """
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is not a valid directory.", file=sys.stderr)
        return 66
    if _git(["rev-parse", "--is-inside-work-tree"], target_abs).returncode != 0:
        print(f"Error: '{target_abs}' is not a git work tree; refusing to run a keep-or-revert "
              "loop with no way to roll back.", file=sys.stderr)
        return 66

    paths = paths or []
    signal = " ".join(cmdv)
    print(f"[autoevolve loop] Running signal verification: {signal}")
    run_quiet_script = os.path.join(SCRIPTS_DIR, "run_quiet.py")
    # Pass argv through `--` so the child receives the arguments exactly as given.
    res = subprocess.run([sys.executable, run_quiet_script, "--", *cmdv], cwd=target_abs)

    if res.returncode == 0:
        print("\n======================================================================")
        print(" [ PASS ] SIGNAL VERIFIED: Test / Benchmark Command Succeeded!")
        print("======================================================================")
        desc = message or f"kept experiment ({signal} pass)"
        commit_ref = "HEAD"
        if auto_commit:
            if not paths:
                print("[autoevolve loop] --auto-commit needs --paths: refusing to run "
                      "`git add .`, which would commit unrelated work.", file=sys.stderr)
                return 2
            _git(["add", "--", *paths], target_abs, "staging experiment paths")
            committed = _git(["commit", "-m", f"evolve: {desc}"], target_abs, "commit")
            if committed.returncode != 0:
                return 1
            # Journal the sha that now exists, not the literal "HEAD" recorded before committing.
            commit_ref = _git(["rev-parse", "--short", "HEAD"], target_abs).stdout.strip() or "HEAD"
        cmd_journal(target_abs, commit=commit_ref, signal=signal, action="keep", changed=desc,
                    why="Signal check passed")
        return 0

    print("\n======================================================================")
    print(" [ FAIL ] SIGNAL REGRESSED: Test / Benchmark Command Failed!")
    print("======================================================================")
    if not paths:
        print("[autoevolve loop] No --paths declared, so the tree is left untouched. Reverting "
              "without knowing which files the experiment touched would risk destroying work "
              "this loop did not create. Current state:", file=sys.stderr)
        print(_git(["status", "--porcelain=v1"], target_abs).stdout, file=sys.stderr)
        return 2
    print(f"[autoevolve loop] Reverting only the declared experiment paths ({len(paths)}):")
    _revert_paths(target_abs, paths)
    cmd_journal(target_abs, commit="HEAD", signal=signal, action="revert",
                changed=message or "failed hypothesis", why="Signal regressed")
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="AutoEvolve CLI: Install, initialize, setup, and check mindset readiness in any project.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # install command
    p_install = subparsers.add_parser("install", help="Install AGENTS.md & adapters into target repo")
    p_install.add_argument("--target", required=True, help="Target project directory path")
    p_install.add_argument("--dry-run", action="store_true", help="Preview files to be installed without modifying disk")

    # init command
    p_init = subparsers.add_parser("init", help="Scaffold DIRECTION.md & JOURNAL.md templates into target repo")
    p_init.add_argument("--target", required=True, help="Target project directory path")

    # check command
    p_check = subparsers.add_parser("check", help="Check target repository readiness for AutoEvolve sessions")
    p_check.add_argument("--target", required=True, help="Target project directory path")

    # setup command
    p_setup = subparsers.add_parser("setup", help="One-command full setup: install AGENTS.md, scaffold templates, and detect stack")
    p_setup.add_argument("--target", required=True, help="Target project directory path")

    # journal command
    p_journal = subparsers.add_parser("journal", help="Append a structured experiment log entry to JOURNAL.md")
    p_journal.add_argument("--target", required=True, help="Target project directory path")
    p_journal.add_argument("--commit", required=True, help="Git commit hash or 'HEAD'")
    p_journal.add_argument("--signal", required=True, help="Signal measured (e.g. '31/31 tests pass')")
    p_journal.add_argument("--action", choices=["keep", "revert"], required=True, help="Keep or revert decision")
    p_journal.add_argument("--changed", required=True, help="Short summary of what changed")
    p_journal.add_argument("--why", required=True, help="Rationale for decision")

    # hooks command
    p_hooks = subparsers.add_parser("hooks", help="Install zero-dependency pre-commit hook into target repository")
    p_hooks.add_argument("--target", required=True, help="Target project directory path")
    p_hooks.add_argument("--force", action="store_true",
                         help="Overwrite an existing pre-commit hook (a .autoevolve-backup copy is kept)")

    # loop command
    p_loop = subparsers.add_parser(
        "loop", help="Run the signal, then keep or revert only the declared experiment paths",
        epilog="Example:\n"
               "  python autoevolve.py loop --target . --paths src/api.py --auto-commit "
               "-- pytest -k \"not slow\"",
    )
    p_loop.add_argument("--target", required=True, help="Target project directory path")
    p_loop.add_argument("--cmd", help="Verification command as one string. Split with POSIX rules, "
                                      "so prefer the `-- <argv>` form for anything containing "
                                      "quotes or Windows paths.")
    p_loop.add_argument("--paths", action="append", default=[], metavar="PATH",
                        help="A path this experiment created or edited (repeatable). Required "
                             "before this command will revert or commit anything: it never "
                             "guesses which edits are yours.")
    p_loop.add_argument("--message", help="Description of hypothesis / change")
    p_loop.add_argument("--auto-commit", action="store_true", help="Commit the declared paths if the signal passes")
    p_loop.add_argument("cmdv", nargs=argparse.REMAINDER,
                        help="The verification command, after `--`. Passed through verbatim.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 64

    if args.command == "install":
        return cmd_install(args.target, args.dry_run)
    elif args.command == "init":
        return cmd_init(args.target)
    elif args.command == "check":
        return cmd_check(args.target)
    elif args.command == "setup":
        return cmd_setup(args.target)
    elif args.command == "journal":
        return cmd_journal(args.target, args.commit, args.signal, args.action, args.changed, args.why)
    elif args.command == "hooks":
        return cmd_hooks(args.target, args.force)
    elif args.command == "loop":
        cmdv = [a for a in args.cmdv if a != "--"]
        if not cmdv and args.cmd:
            cmdv = shlex.split(args.cmd)
        if not cmdv:
            p_loop.error("give the verification command after `--`, or via --cmd")
        return cmd_loop(args.target, cmdv, args.message, args.auto_commit, args.paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
