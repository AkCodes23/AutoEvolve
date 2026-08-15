"""Exhaustive integration tests for PowerShell and POSIX installers."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTALL_PS1 = os.path.join(REPO_ROOT, "install.ps1")
INSTALL_SH = os.path.join(REPO_ROOT, "install.sh")


def run_ps1(target_dir: str, force: bool = False) -> subprocess.CompletedProcess:
    """Helper to run install.ps1 against a target directory."""
    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        INSTALL_PS1,
        "-TargetDir",
        target_dir,
    ]
    if force:
        cmd.append("-Force")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestPowerShellInstaller:
    def test_default_installation_creates_core_and_claude_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = run_ps1(tmp)
            assert res.returncode == 0, f"Installer failed: {res.stderr}"

            assert os.path.isfile(os.path.join(tmp, "AGENTS.md"))
            assert os.path.isfile(os.path.join(tmp, "DIRECTION.md"))
            assert os.path.isfile(os.path.join(tmp, "JOURNAL.md"))
            assert os.path.isfile(os.path.join(tmp, "CLAUDE.md"))

    def test_cursor_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".cursor"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".cursor", "rules", "autoevolve.mdc"))

    def test_windsurf_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, ".windsurfrules"), "w") as f:
                f.write("# existing")
            res = run_ps1(tmp, force=True)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".windsurfrules"))
            with open(os.path.join(tmp, ".windsurfrules"), "r", encoding="utf-8") as f:
                assert "<autoevolve_mindset>" in f.read()

    def test_github_copilot_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".github"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".github", "copilot-instructions.md"))

    def test_cline_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, ".clinerules"), "w") as f:
                f.write("# old")
            res = run_ps1(tmp, force=True)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".clinerules"))

    def test_continue_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".continue"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".continue", "prompts", "autoevolve.prompt"))

    def test_zed_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".zed"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".zed", "rules.md"))

    def test_jetbrains_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".idea"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".jetbrains", "ai-instructions.md"))

    def test_cody_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".cody"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".cody", "instructions.md"))

    def test_openhands_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".openhands"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, ".openhands", "instructions.md"))

    def test_gemini_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".gemini"))
            res = run_ps1(tmp)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(tmp, "GEMINI.md"))

    def test_preserves_existing_direction_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom_text = "# Custom User Goal: Optimize Speed to <10ms"
            direction_file = os.path.join(tmp, "DIRECTION.md")
            with open(direction_file, "w", encoding="utf-8") as f:
                f.write(custom_text)

            res = run_ps1(tmp, force=False)
            assert res.returncode == 0
            with open(direction_file, "r", encoding="utf-8") as f:
                assert f.read() == custom_text

    def test_force_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            direction_file = os.path.join(tmp, "DIRECTION.md")
            with open(direction_file, "w", encoding="utf-8") as f:
                f.write("# Outdated content")

            res = run_ps1(tmp, force=True)
            assert res.returncode == 0
            with open(direction_file, "r", encoding="utf-8") as f:
                assert "## Objective" in f.read()

    def test_handles_target_path_with_spaces(self):
        with tempfile.TemporaryDirectory() as base_tmp:
            space_dir = os.path.join(base_tmp, "path with spaces and symbols")
            os.makedirs(space_dir)
            res = run_ps1(space_dir)
            assert res.returncode == 0
            assert os.path.isfile(os.path.join(space_dir, "AGENTS.md"))
