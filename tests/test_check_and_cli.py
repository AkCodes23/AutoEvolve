"""Tests for scripts/check.py and autoevolve.py CLI."""
from __future__ import annotations

import os
import subprocess
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.check import (
    check_mindset_budgets,
    check_adapters_in_sync,
    check_wayfinder_direction_map,
    check_python_syntax,
    run_all_checks,
)


class TestCheckAndCLI:
    def test_mindset_budgets_pass(self):
        agents_path = os.path.join(REPO_ROOT, "AGENTS.md")
        passed, errors = check_mindset_budgets(agents_path)
        assert passed, f"Mindset budget violations: {errors}"

    def test_adapters_in_sync(self):
        passed, errors = check_adapters_in_sync(REPO_ROOT)
        assert passed, f"Adapter synchronization errors: {errors}"

    def test_wayfinder_direction_map(self):
        passed, errors = check_wayfinder_direction_map(REPO_ROOT)
        assert passed, f"DIRECTION.md errors: {errors}"

    def test_python_syntax_integrity(self):
        passed, errors = check_python_syntax(REPO_ROOT)
        assert passed, f"Syntax errors: {errors}"

    def test_run_all_checks_overall(self):
        assert run_all_checks(REPO_ROOT) is True

    def test_autoevolve_cli_help(self):
        cli_path = os.path.join(REPO_ROOT, "autoevolve.py")
        res = subprocess.run([sys.executable, cli_path, "--help"], capture_output=True, text=True)
        assert res.returncode == 0
        assert "AutoEvolve" in res.stdout
        assert "check" in res.stdout
        assert "map" in res.stdout
        assert "bench" in res.stdout
