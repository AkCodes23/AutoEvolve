#!/usr/bin/env python3
"""Pre-flight Target Repository Checker for AutoEvolve.

Validates whether a target repository is ready for AI coding agent sessions using AutoEvolve.
Usage:
    python scripts/check_target.py --target /path/to/project
"""
import argparse
import os
import subprocess
import sys


def check_target(target_dir: str) -> dict:
    target_abs = os.path.abspath(target_dir)
    results = {
        "target": target_abs,
        "exists": os.path.isdir(target_abs),
        "is_git": False,
        "agents_installed": False,
        "core_fingerprint": False,
        "direction_present": False,
        "journal_present": False,
        "has_test_runner": False,
        "detected_stack": [],
        "score": 0,
        "recommendations": [],
    }

    if not results["exists"]:
        results["recommendations"].append(f"Create or specify a valid directory path (path '{target_abs}' not found).")
        return results

    # 1. Git Check
    git_dir = os.path.join(target_abs, ".git")
    if os.path.exists(git_dir):
        results["is_git"] = True
    else:
        res = subprocess.run(["git", "-C", target_abs, "rev-parse", "--git-dir"], capture_output=True, text=True)
        results["is_git"] = (res.returncode == 0)

    if not results["is_git"]:
        results["recommendations"].append("Run 'git init' in the target project to enable keep-or-revert experiments.")

    # 2. AGENTS.md & Fingerprint Check
    agents_path = os.path.join(target_abs, "AGENTS.md")
    if os.path.isfile(agents_path):
        results["agents_installed"] = True
        try:
            with open(agents_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                results["core_fingerprint"] = ("AutoEvolve-Core" in content) or ("AutoEvolve" in content)
        except Exception:
            pass

    if not results["agents_installed"]:
        results["recommendations"].append("Run 'python autoevolve.py install --target <path>' to install AGENTS.md.")
    elif not results["core_fingerprint"]:
        results["recommendations"].append("AGENTS.md exists but lacks AutoEvolve fingerprint. Re-install with --profile core or full.")

    # 3. DIRECTION.md Check
    direction_path = os.path.join(target_abs, "DIRECTION.md")
    results["direction_present"] = os.path.isfile(direction_path)
    if not results["direction_present"]:
        results["recommendations"].append("Run 'python autoevolve.py init --target <path>' to scaffold DIRECTION.md.")

    # 4. JOURNAL.md Check
    journal_path = os.path.join(target_abs, "JOURNAL.md")
    results["journal_present"] = os.path.isfile(journal_path)
    if not results["journal_present"]:
        results["recommendations"].append("Run 'python autoevolve.py init --target <path>' to scaffold JOURNAL.md.")

    # 5. Test Runner & Tech Stack Detection
    stack_signals = [
        ("python/pytest", ["pytest.ini", "setup.py", "pyproject.toml", "requirements.txt", "tox.ini"]),
        ("javascript/npm", ["package.json"]),
        ("rust/cargo", ["Cargo.toml"]),
        ("go/modules", ["go.mod"]),
        ("make/c", ["Makefile", "CMakeLists.txt"]),
    ]

    for stack_name, files in stack_signals:
        for fname in files:
            if os.path.isfile(os.path.join(target_abs, fname)):
                results["detected_stack"].append(stack_name)
                results["has_test_runner"] = True
                break

    if not results["has_test_runner"]:
        results["recommendations"].append("Add a test runner or build script (e.g., pytest, npm test, Makefile) to serve as a baseline signal.")

    # Calculate Readiness Score (0-100%)
    score = 0
    if results["is_git"]:
        score += 25
    if results["agents_installed"] and results["core_fingerprint"]:
        score += 35
    elif results["agents_installed"]:
        score += 20
    if results["direction_present"]:
        score += 15
    if results["journal_present"]:
        score += 10
    if results["has_test_runner"]:
        score += 15

    results["score"] = min(score, 100)
    return results


def print_report(res: dict):
    print("=" * 70)
    print(f"AUTOEVOLVE TARGET REPOSITORY READINESS CHECK")
    print("=" * 70)
    print(f"Target Directory : {res['target']}")
    print(f"Readiness Score  : {res['score']}% / 100%")
    print("-" * 70)
    print(f"  [ {'OK' if res['is_git'] else 'FAIL'} ] Git Repository Initialized")
    print(f"  [ {'OK' if res['agents_installed'] else 'FAIL'} ] AGENTS.md Present")
    print(f"  [ {'OK' if res['core_fingerprint'] else 'WARN'} ] AutoEvolve Fingerprint Present")
    print(f"  [ {'OK' if res['direction_present'] else 'WARN'} ] DIRECTION.md Scaffolding")
    print(f"  [ {'OK' if res['journal_present'] else 'WARN'} ] JOURNAL.md Scaffolding")
    print(f"  [ {'OK' if res['has_test_runner'] else 'WARN'} ] Test Runner / Baseline Signal ({', '.join(res['detected_stack']) or 'None'})")
    print("-" * 70)

    if res["recommendations"]:
        print("ACTIONABLE SETUP INSTRUCTIONS:")
        for idx, rec in enumerate(res["recommendations"], 1):
            print(f"  {idx}. {rec}")
    else:
        print("STATUS: Target repository is 100% READY for AutoEvolve AI coding sessions!")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Check target repository readiness for AutoEvolve.")
    parser.add_argument("--target", required=True, help="Path to target project directory")
    parser.add_argument("--fix", action="store_true", help="Automatically install AGENTS.md and scaffold templates if missing")
    args = parser.parse_args()

    results = check_target(args.target)
    if args.fix and results["score"] < 100:
        print("\n[check_target] Applying automatic --fix setup...")
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if here not in sys.path:
            sys.path.insert(0, here)
        import autoevolve
        autoevolve.cmd_setup(args.target)
        results = check_target(args.target)

    print_report(results)
    return 0 if results["score"] >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
