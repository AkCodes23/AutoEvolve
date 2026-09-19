import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


class InstallerTests(unittest.TestCase):
    workspace: tempfile.TemporaryDirectory[str]
    source: Path
    target: Path
    base: Path
    log: Path
    bin: Path
    env: dict[str, str]
    engine: str

    def setUp(self) -> None:
        if not shutil.which(self.engine):
            self.skipTest(f"{self.engine} is not available")
        if os.name == "nt" and self.engine == "sh":
            self.skipTest("Use native PowerShell on Windows")
        self.workspace = tempfile.TemporaryDirectory(prefix="autoevolve-test-", dir=Path.home())
        self.addCleanup(self.workspace.cleanup)
        self.base = Path(self.workspace.name)
        self.source = self.base / "source checkout"
        shutil.copytree(
            ROOT,
            self.source,
            ignore=shutil.ignore_patterns(".git", ".venv", ".autoevolve", "*cache*", "*.pyc"),
        )
        self.target = self.base / "target with spaces [brackets]"
        self.target.mkdir()
        self.log = self.base / "requests"
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name in ("curl", "wget"):
            shutil.copyfile(ROOT / "tests/fixtures/download.py", self.bin / name)
            (self.bin / name).chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
            "FIXTURE_SOURCE": str(self.source),
            "REQUEST_LOG": str(self.log),
        }
        for key in ("AUTOEVOLVE_REF", "FAIL_FILE", "CORRUPT_FILE", "FAIL_RESOLVE"):
            self.env.pop(key, None)

    def run_installer(
        self,
        *,
        agents: str | None = None,
        force: bool = False,
        mode: str = "local",
        expected: int | None = 0,
        target: Path | None = None,
        ref: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        target = target or self.target
        extension = "sh" if self.engine == "sh" else "ps1"
        script = self.source / f"install.{extension}"
        if mode == "remote":
            script = self.base / f"downloaded.{extension}"
            shutil.copyfile(self.source / f"install.{extension}", script)
        input_text = None
        if self.engine == "sh":
            command = [self.engine, str(script)] if mode != "pipe" else [self.engine, "-s", "--"]
            command.append(str(target))
            if agents is not None:
                command += ["--agents", agents]
            if force:
                command.append("--force")
            if ref:
                command += ["--ref", ref]
            if mode == "pipe":
                input_text = script.read_text(encoding="utf-8")
        else:
            mock = ps_quote(str(ROOT / "tests/fixtures/download.ps1"))
            if mode == "pipe":
                invocation = f"Get-Content -LiteralPath {ps_quote(str(script))} -Raw | Invoke-Expression"
            else:
                invocation = f"& {ps_quote(str(script))} -TargetDir {ps_quote(str(target))}"
                if agents is not None:
                    invocation += f" -Agents {ps_quote(agents)}"
                if force:
                    invocation += " -Force"
                if ref:
                    invocation += f" -Ref {ps_quote(ref)}"
            command = [
                self.engine,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"$ErrorActionPreference = 'Stop'; . {mock}; {invocation}; if ($LASTEXITCODE) {{ exit $LASTEXITCODE }}",
            ]
        result = subprocess.run(
            command,
            cwd=target,
            env=self.env,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
            check=False,
        )
        if expected is not None:
            self.assertEqual(result.returncode, expected, result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((target / ".autoevolve/install.lock").exists(), result.stdout)
        self.assertEqual(list((target / ".autoevolve").glob("staging.*")), [])
        self.assertEqual(list(target.rglob(".autoevolve.*")), [])
        return result

    def test_fresh_offline_install_and_repeat(self) -> None:
        first = self.run_installer()
        for name in ("AGENTS.md", "CLAUDE.md", "DIRECTION.md", "JOURNAL.md", "CONSTRAINTS.md"):
            self.assertTrue((self.target / name).is_file())
        self.assertIn("[installed]", first.stdout)
        second = self.run_installer(force=True)
        self.assertIn("[current] AGENTS.md", second.stdout)
        self.assertFalse(self.log.exists(), "Local installs must work without network access")

    def test_install_into_source_is_noop(self) -> None:
        result = self.run_installer(target=self.source, agents="generic", force=True)
        self.assertIn("[current] AGENTS.md", result.stdout)

    def test_claude_is_not_suppressed_by_github(self) -> None:
        (self.target / ".github").mkdir()
        self.run_installer()
        self.assertTrue((self.target / "CLAUDE.md").exists())

    def test_all_adapter_destinations_and_coexistence(self) -> None:
        manifest = json.loads((self.source / "adapters/manifest.json").read_text(encoding="utf-8"))
        entries = manifest["adapters"]
        existing = self.target / ".github/copilot-instructions.md"
        existing.parent.mkdir()
        existing.write_text("User rules", encoding="utf-8")
        (self.target / ".clinerules").mkdir()
        (self.target / ".clinerules/user.md").write_text("User Cline rules", encoding="utf-8")
        self.run_installer(agents=",".join(entry["id"] for entry in entries))
        for entry in entries:
            self.assertEqual(
                (self.target / entry["destination"]).read_bytes(),
                (self.source / entry["source"]).read_bytes(),
            )
        self.assertEqual(existing.read_text(encoding="utf-8"), "User rules")
        self.assertEqual(
            (self.target / ".clinerules/user.md").read_text(encoding="utf-8"), "User Cline rules"
        )

    def test_unknown_selection_does_not_install(self) -> None:
        self.run_installer(agents="missing-agent", expected=None)
        self.assertFalse((self.target / "DIRECTION.md").exists())

    def test_explicit_selection_excludes_defaults(self) -> None:
        self.run_installer(agents="aider")
        self.assertTrue((self.target / "CONVENTIONS.md").exists())
        self.assertFalse((self.target / "AGENTS.md").exists())
        self.assertFalse((self.target / "CLAUDE.md").exists())

    def test_existing_files_are_preserved_even_with_force(self) -> None:
        names = ("AGENTS.md", "CLAUDE.md", "DIRECTION.md", "JOURNAL.md", "CONSTRAINTS.md")
        for name in names:
            (self.target / name).write_text("User-owned " + name, encoding="utf-8")
        result = self.run_installer(force=True, expected=2)
        self.assertNotIn("Files installed or already current", result.stdout)
        self.assertIn("[manual integration required]", result.stdout)
        for name in names:
            self.assertEqual((self.target / name).read_text(encoding="utf-8"), "User-owned " + name)

    def test_edited_managed_file_is_preserved(self) -> None:
        self.run_installer(agents="generic")
        path = self.target / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nUser edits\n", encoding="utf-8")
        original = path.read_bytes()
        self.run_installer(agents="generic", force=True, expected=2)
        self.assertEqual(path.read_bytes(), original)

    def test_force_upgrade_requires_receipt_and_creates_backup(self) -> None:
        self.run_installer(agents="generic")
        old = (self.target / "AGENTS.md").read_bytes()
        direction = self.target / "DIRECTION.md"
        direction.write_text("My actual goal", encoding="utf-8")
        protocol = self.source / "PROTOCOL.md"
        protocol.write_text(protocol.read_text(encoding="utf-8") + "\nNew instruction.\n", encoding="utf-8")
        subprocess.run([sys.executable, str(self.source / "scripts/build_adapters.py")], check=True)
        self.run_installer(agents="generic", expected=2)
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), old)
        self.run_installer(agents="generic", force=True)
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), (self.source / "AGENTS.md").read_bytes())
        backups = list((self.target / ".autoevolve/backups").rglob("AGENTS.md"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), old)
        self.assertEqual(direction.read_text(encoding="utf-8"), "My actual goal")

    def test_remote_installs_use_one_commit(self) -> None:
        self.run_installer(mode="remote")
        urls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum("/commits/main" in url for url in urls), 1)
        self.assertTrue(all(f"/{SHA}/" in url for url in urls if "raw.githubusercontent.com" in url))

    def test_explicit_commit_skips_resolution(self) -> None:
        self.run_installer(mode="remote", ref=SHA)
        self.assertNotIn("/commits/main", self.log.read_text(encoding="utf-8"))

    def test_rate_limit_has_actionable_recovery(self) -> None:
        self.env["FAIL_RESOLVE"] = "1"
        result = self.run_installer(mode="remote", expected=None)
        self.assertIn("FULL_COMMIT_SHA", result.stdout)
        self.assertFalse((self.target / "AGENTS.md").exists())
        self.run_installer(mode="remote", ref=SHA)

    def test_piped_execution(self) -> None:
        self.run_installer(mode="pipe")
        self.assertTrue((self.target / "CLAUDE.md").exists())
        self.assertTrue(self.log.exists(), "Piped scripts must fetch remote distribution")

    def test_interrupted_download_leaves_no_final_files_and_retry_repairs(self) -> None:
        self.env["FAIL_FILE"] = "adapters/claude.md"
        self.run_installer(mode="remote", expected=None)
        for name in ("AGENTS.md", "CLAUDE.md", "DIRECTION.md"):
            self.assertFalse((self.target / name).exists())
        del self.env["FAIL_FILE"]
        self.run_installer(mode="remote")
        self.assertEqual(
            (self.target / "CLAUDE.md").read_bytes(), (self.source / "adapters/claude.md").read_bytes()
        )

    def test_checksum_failure_preserves_existing_files(self) -> None:
        self.run_installer()
        old = (self.target / "AGENTS.md").read_bytes()
        self.env.update(FAIL_FILE="adapters/claude.md", CORRUPT_FILE="1")
        result = self.run_installer(mode="remote", force=True, expected=None)
        self.assertIn("Checksum mismatch", result.stdout)
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), old)

    def test_legacy_cline_file_is_preserved(self) -> None:
        legacy = self.target / ".clinerules"
        legacy.write_text("Legacy user rules", encoding="utf-8")
        self.run_installer(agents="cline", expected=2)
        self.assertEqual(legacy.read_text(encoding="utf-8"), "Legacy user rules")

    def test_symbolic_link_is_not_followed(self) -> None:
        if os.name == "nt":
            self.skipTest("Windows symlinks require elevated privileges; junction covered separately")
        outside = self.base / "outside"
        outside.mkdir()
        (self.target / ".cursor").symlink_to(outside, target_is_directory=True)
        self.run_installer(agents="cursor", expected=None)
        self.assertEqual(list(outside.iterdir()), [])

    def test_windows_junction_is_not_followed(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows-only junction")
        outside = self.base / "outside"
        outside.mkdir()
        subprocess.run(
            [
                self.engine,
                "-NoProfile",
                "-Command",
                f"New-Item -ItemType Junction -Path {ps_quote(str(self.target / '.cursor'))} "
                f"-Target {ps_quote(str(outside))} | Out-Null",
            ],
            check=True,
        )
        self.run_installer(agents="cursor", expected=None)
        self.assertEqual(list(outside.iterdir()), [])


class PosixInstallerTests(InstallerTests):
    engine = "sh"


class PowerShellInstallerTests(InstallerTests):
    engine = "pwsh"


class WindowsPowerShellInstallerTests(InstallerTests):
    engine = "powershell"


class DistributionTests(unittest.TestCase):
    def test_generated_files_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_adapters.py"), "--check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_manifest_metadata_and_frontmatter(self) -> None:
        manifest = json.loads((ROOT / "adapters/manifest.json").read_text(encoding="utf-8"))
        ids: set[str] = set()
        for entry in manifest["adapters"]:
            self.assertNotIn(entry["id"], ids)
            ids.add(entry["id"])
            self.assertIn(entry["load_mode"], ("automatic", "manual"))
            self.assertTrue(entry["activation"])
            self.assertTrue(entry["versions"])
            self.assertTrue(entry["documentation"].startswith("https://"))
            if entry["frontmatter"]:
                self.assertTrue((ROOT / entry["source"]).read_bytes().startswith(b"---\n"))

    def test_checksum_manifest_covers_payloads(self) -> None:
        for line in (ROOT / "checksums.txt").read_text(encoding="utf-8").splitlines():
            expected, path = line.split("  ", 1)
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)


def load_tests(
    loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
    return unittest.TestSuite(
        loader.loadTestsFromTestCase(case)
        for case in (
            DistributionTests,
            PosixInstallerTests,
            PowerShellInstallerTests,
            WindowsPowerShellInstallerTests,
        )
    )


if __name__ == "__main__":
    unittest.main()
