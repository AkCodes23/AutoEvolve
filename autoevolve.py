#!/usr/bin/env python3
"""AutoEvolve Universal Cross-Platform CLI Tool.

Enables installation, template initialization, and readiness checking of the AutoEvolve
mindset in ANY target repository across Windows, macOS, and Linux.

Usage:
    python autoevolve.py install --target /path/to/project [--profile core|full] [--dry-run]
    python autoevolve.py init --target /path/to/project
    python autoevolve.py check --target /path/to/project
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "scripts")
TEMPLATES_DIR = os.path.join(HERE, "templates")


def cmd_install(target: str, profile: str = "core", dry_run: bool = False) -> int:
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs):
        print(f"Error: Target path '{target_abs}' does not exist.", file=sys.stderr)
        return 66
    elif not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is a file, not a directory.", file=sys.stderr)
        return 66

    print(f"[autoevolve] Installing AutoEvolve ({profile} profile) into target: {target_abs}")

    # Use native PowerShell script on Windows, or shell script / Python fallback
    if sys.platform == "win32":
        ps_script = os.path.join(HERE, "install.ps1")
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script, "-Target", target_abs, "-Profile", profile]
        if dry_run:
            cmd.append("-DryRun")
        res = subprocess.run(cmd, timeout=120)
        return res.returncode
    else:
        sh_script = os.path.join(HERE, "install.sh")
        bash_bin = shutil.which("bash") or "sh"
        cmd = [bash_bin, sh_script, "--target", target_abs, "--profile", profile]
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


def cmd_setup(target: str, profile: str = "core") -> int:
    """One-command full setup: install AGENTS.md/adapters, scaffold templates, and detect stack."""
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is not a valid directory.", file=sys.stderr)
        return 66

    print(f"[autoevolve] Running one-command setup for target: {target_abs}")
    rc_inst = cmd_install(target_abs, profile=profile)
    rc_init = cmd_init(target_abs)

    detected = "manual test command"
    if os.path.exists(os.path.join(target_abs, "pytest.ini")) or os.path.exists(os.path.join(target_abs, "tests")):
        detected = "pytest tests/"
    elif os.path.exists(os.path.join(target_abs, "package.json")):
        detected = "npm test"
    elif os.path.exists(os.path.join(target_abs, "Cargo.toml")):
        detected = "cargo test"
    elif os.path.exists(os.path.join(target_abs, "go.mod")):
        detected = "go test ./..."

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

    print(f"[autoevolve] Setup complete! Suggested test signal for DIRECTION.md: '{detected}'")
    return 0 if (rc_inst == 0 and rc_init == 0) else 1


def cmd_journal(target: str, commit: str, signal: str, action: str, changed: str, why: str) -> int:
    """Append a structured experiment log line to JOURNAL.md."""
    target_abs = os.path.abspath(target)
    journal_path = os.path.join(target_abs, "JOURNAL.md")
    if not os.path.exists(journal_path):
        cmd_init(target_abs)

    entry = f"- {commit} · {signal} · {action.lower()} · {changed} · {why}\n"
    with open(journal_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[autoevolve] Journal entry appended to {journal_path}:\n  {entry.strip()}")
    return 0


def cmd_hooks(target: str) -> int:
    """Install zero-dependency pre-commit hook into target repository."""
    target_abs = os.path.abspath(target)
    hooks_dir = os.path.join(target_abs, ".git", "hooks")
    if not os.path.exists(hooks_dir):
        print(f"Error: Target path '{target_abs}' is not a git repository root (no .git/hooks found).", file=sys.stderr)
        return 66

    hook_path = os.path.join(hooks_dir, "pre-commit")
    script_content = (
        "#!/bin/sh\n"
        "# AutoEvolve pre-commit hook: enforces adapter checksum and invariant checks.\n"
        "echo '[autoevolve pre-commit] Running invariant checks...'\n"
        "if [ -f \"scripts/check.py\" ]; then\n"
        "    python3 scripts/check.py || exit 1\n"
        "fi\n"
        "if [ -f \"scripts/build_adapters.py\" ]; then\n"
        "    python3 scripts/build_adapters.py --check || exit 1\n"
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


def cmd_loop(target: str, cmd: str, message: str | None = None, auto_commit: bool = False) -> int:
    """Automate interactive keep-or-revert experiment loop."""
    target_abs = os.path.abspath(target)
    if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
        print(f"Error: Target path '{target_abs}' is not a valid directory.", file=sys.stderr)
        return 66

    print(f"[autoevolve loop] Running signal verification: {cmd}")
    run_quiet_script = os.path.join(SCRIPTS_DIR, "run_quiet.py")
    res = subprocess.run([sys.executable, run_quiet_script, cmd], cwd=target_abs)

    if res.returncode == 0:
        print("\n======================================================================")
        print(" [ PASS ] SIGNAL VERIFIED: Test / Benchmark Command Succeeded!")
        print("======================================================================")
        desc = message or f"kept experiment ({cmd} pass)"
        cmd_journal(target_abs, commit="HEAD", signal=cmd, action="keep", changed=desc, why="Signal check passed")
        if auto_commit:
            print("[autoevolve loop] Auto-committing kept experiment to git...")
            subprocess.run(["git", "add", "."], cwd=target_abs)
            subprocess.run(["git", "commit", "-m", f"evolve: {desc}"], cwd=target_abs)
        return 0
    else:
        print("\n======================================================================")
        print(" [ FAIL ] SIGNAL REGRESSED: Test / Benchmark Command Failed!")
        print("======================================================================")
        print("[autoevolve loop] Performing clean git rollback (reverting modified files)...")
        subprocess.run(["git", "checkout", "--", "."], cwd=target_abs)
        cmd_journal(target_abs, commit="HEAD", signal=cmd, action="revert", changed=message or "failed hypothesis", why="Signal regressed")
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
    p_install.add_argument("--profile", choices=["core", "full"], default="core", help="Profile to install (default: core)")
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
    p_setup.add_argument("--profile", choices=["core", "full"], default="core", help="Profile to install (default: core)")

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

    # loop command
    p_loop = subparsers.add_parser("loop", help="Automate interactive keep-or-revert experiment loop")
    p_loop.add_argument("--target", required=True, help="Target project directory path")
    p_loop.add_argument("--cmd", required=True, help="Test / benchmark verification command (e.g. 'pytest tests/')")
    p_loop.add_argument("--message", help="Description of hypothesis / change")
    p_loop.add_argument("--auto-commit", action="store_true", help="Automatically commit to git if signal passes")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 64

    if args.command == "install":
        return cmd_install(args.target, args.profile, args.dry_run)
    elif args.command == "init":
        return cmd_init(args.target)
    elif args.command == "check":
        return cmd_check(args.target)
    elif args.command == "setup":
        return cmd_setup(args.target, args.profile)
    elif args.command == "journal":
        return cmd_journal(args.target, args.commit, args.signal, args.action, args.changed, args.why)
    elif args.command == "hooks":
        return cmd_hooks(args.target)
    elif args.command == "loop":
        return cmd_loop(args.target, args.cmd, args.message, args.auto_commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
