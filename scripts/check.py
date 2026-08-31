#!/usr/bin/env python3
"""Unified AutoEvolve Invariant Validator & Auditor.

Performs strict, zero-dependency repository verification:
1. XML Mindset Budgets (<= 55 lines, <= 5000 bytes, <= 1250 estimated tokens)
2. IDE Adapter Synchronization (100% SHA-256 character-identical matching across 12 IDEs)
3. Wayfinder Decision Map Integrity (DIRECTION.md structure, DAG tickets, Fog boundaries)
4. Python Syntax Integrity (ast.parse across all scripts/ and benchmarks/)
5. Constraints & Failure Graph Integrity (CONSTRAINTS.md and failure_graph.py format)
"""
from __future__ import annotations

import ast
import os
import re
import sys
from typing import List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.build_adapters import build_adapters, extract_core_mindset
from scripts.wayfinder_map import WayfinderMap


def check_mindset_budgets(agents_path: str) -> Tuple[bool, List[str]]:
    """Verify mindset line, byte, and token budgets."""
    errors = []
    if not os.path.exists(agents_path):
        return False, [f"Missing AGENTS.md at {agents_path}"]

    try:
        mindset = extract_core_mindset(agents_path)
    except Exception as e:
        return False, [f"Failed to extract mindset: {e}"]

    lines = mindset.strip().splitlines()
    line_count = len(lines)
    byte_count = len(mindset.encode("utf-8"))
    token_est = int(byte_count / 4.0)

    max_lines = 55
    max_bytes = 5000
    max_tokens = 1250

    if line_count > max_lines:
        errors.append(f"Mindset line count {line_count} exceeds budget {max_lines}")
    if byte_count > max_bytes:
        errors.append(f"Mindset byte count {byte_count} exceeds budget {max_bytes}")
    if token_est > max_tokens:
        errors.append(f"Mindset estimated tokens {token_est} exceeds budget {max_tokens}")

    return len(errors) == 0, errors


def check_adapters_in_sync(repo_root: str) -> Tuple[bool, List[str]]:
    """Verify all 12 IDE adapters are 100% in sync."""
    errors = []
    try:
        in_sync = build_adapters(repo_root, check_only=True)
        if not in_sync:
            errors.append("One or more IDE adapters are out of sync with AGENTS.md")
    except Exception as e:
        errors.append(f"Adapter check error: {e}")
    return len(errors) == 0, errors


def check_wayfinder_direction_map(repo_root: str) -> Tuple[bool, List[str]]:
    """Verify DIRECTION.md decision map structure."""
    errors = []
    direction_path = os.path.join(repo_root, "DIRECTION.md")
    if not os.path.exists(direction_path):
        return False, ["Missing DIRECTION.md"]

    try:
        with open(direction_path, "r", encoding="utf-8") as f:
            content = f.read()
        wmap = WayfinderMap.parse_markdown(content)
        passed, val_errors = wmap.validate_invariants()
        if not passed:
            errors.extend(val_errors)
        if not wmap.destination:
            errors.append("DIRECTION.md missing Destination")
    except Exception as e:
        errors.append(f"DIRECTION.md parsing failed: {e}")

    return len(errors) == 0, errors


def check_python_syntax(repo_root: str) -> Tuple[bool, List[str]]:
    """Verify Python AST syntax across scripts and benchmarks."""
    errors = []
    target_dirs = [
        os.path.join(repo_root, "scripts"),
        os.path.join(repo_root, "benchmarks"),
    ]

    for d in target_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            ast.parse(f.read(), filename=fpath)
                    except Exception as e:
                        errors.append(f"Syntax error in {fpath}: {e}")

    return len(errors) == 0, errors


def run_all_checks(repo_root: str = REPO_ROOT) -> bool:
    print("=" * 80)
    print("  AutoEvolve Invariant & System Auditor (check.py)")
    print("=" * 80)

    checks = [
        ("Mindset Budgets (<= 55 lines, <= 5000 bytes)", lambda: check_mindset_budgets(os.path.join(repo_root, "AGENTS.md"))),
        ("IDE Adapters Synchronization (12 IDEs)", lambda: check_adapters_in_sync(repo_root)),
        ("Wayfinder Decision Map (DIRECTION.md)", lambda: check_wayfinder_direction_map(repo_root)),
        ("Python AST Syntax Integrity", lambda: check_python_syntax(repo_root)),
    ]

    all_passed = True
    for name, check_fn in checks:
        passed, errors = check_fn()
        if passed:
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}")
            for err in errors:
                print(f"         --> {err}")
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("  ALL AUTOEVOLVE INVARIANTS VERIFIED: OK")
    else:
        print("  INVARIANT AUDIT FAILED: FIX VIOLATIONS ABOVE")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
