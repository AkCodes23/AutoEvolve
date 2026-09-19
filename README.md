# AutoEvolve

A Markdown workflow for AI coding assistants: define one outcome, make a small
change, verify it, and stop when it succeeds or reaches the agreed limits.

AutoEvolve ships instructions and installers. It has no agent runtime, formal
verifier, search engine, or telemetry service. Optional research techniques are
described separately in [advanced usage](docs/advanced.md).

## Install

Run in an existing target project directory. The defaults install `AGENTS.md`,
`CLAUDE.md`, and starter direction, constraint, and journal files. Choose agents
explicitly to install only what you use; selection never depends on IDE markers.

### Linux / macOS

```sh
curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh | sh
```

To choose integrations or a different target, download the installer first:

```sh
curl -fsSL https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.sh -o install-autoevolve.sh
sh install-autoevolve.sh "/path/to/project" --agents claude,cursor
```

### Windows PowerShell (5.1 or 7+)

```powershell
Invoke-RestMethod https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.ps1 | Invoke-Expression
```

```powershell
Invoke-RestMethod https://raw.githubusercontent.com/AkCodes23/AutoEvolve/main/install.ps1 -OutFile install-autoevolve.ps1
.\install-autoevolve.ps1 -TargetDir "C:\path with spaces\project" -Agents claude,cursor
```

Downloading a script executes repository code; inspect it first if required by your
project. For reproducible installs, download the installer from a reviewed full
commit SHA instead of `main`, and pass that same SHA with `--ref SHA` / `-Ref SHA`.
`AUTOEVOLVE_REF` also accepts a full SHA. Remote installs otherwise resolve `main`
once through the GitHub API and fetch all payloads from that immutable commit.
If API access is rate-limited, supply a SHA or use an offline checkout.

### Offline from a checkout

```sh
git clone https://github.com/AkCodes23/AutoEvolve.git
sh AutoEvolve/install.sh "/path/to/project" --agents generic
```

```powershell
.\AutoEvolve\install.ps1 -TargetDir "C:\project" -Agents generic
```

Source files are resolved relative to the saved installer, never the target
directory. No language packages are needed to install: POSIX uses standard shell
utilities, `sha256sum` or macOS `shasum`, and curl/wget for downloads; PowerShell
uses built-in commands. A checkout must include generated distribution files.

## Choose and activate your assistant

Use `--list-agents` / `-ListAgents` to list available IDs, or see the
[compatibility and activation guide](docs/adapters.md). Examples:

```sh
sh AutoEvolve/install.sh . --agents cline,continue,copilot
sh AutoEvolve/install.sh . --agents aider
aider --read CONVENTIONS.md
```

The manifest distinguishes Claude Code, Cursor, Copilot, Cline, Continue, Windsurf,
Gemini CLI, Aider, JetBrains AI Assistant, Junie, Zed, OpenHands, and manual Cody
context. Product variants are not implicitly supported. All integrations are
**experimental** pending live version-specific activation evidence; installer
tests alone cannot prove an IDE loaded a rule.

For each selected agent, follow its activation check before starting a task.
AI Assistant requires setting the rule's activation mode; Aider and Cody require
explicit context loading. Existing rules may have higher precedence. Select only
one entrypoint per host where possible to avoid duplicate prompt context.

## First task

1. Fill in `DIRECTION.md` with the requested outcome, a verification command,
   success criterion, guardrails, and limits. The starter has no project-specific
   objective or claimed test results.
2. Ask the assistant: “Read DIRECTION.md, establish the baseline, and work on this
   objective using AutoEvolve.”
3. Review the actual diff and evidence. The default is one candidate at a time,
   at most three attempts, fifteen elapsed minutes, or two consecutive failures.
   Success stops the loop immediately.

Limits are prompt instructions, not runtime enforcement. Use the host's own time,
token, and spending controls where available. The assistant must disclose missing
verification rather than treating it as a passing check.

## Existing files, upgrades, and recovery

- Existing `DIRECTION.md`, `JOURNAL.md`, and `CONSTRAINTS.md` are always preserved,
  including with `--force` / `-Force`. Review updated templates separately.
- Byte-identical instructions are reported as **current**. Differing instructions
  are a **manual integration required** conflict (exit code 2), not a success.
- `--force` / `-Force` upgrades only unmodified instructions recorded by this
  installer in `.autoevolve/receipts/`. It backs up replaced files under
  `.autoevolve/backups/`. Edited and untracked instructions remain protected.
  Earlier AutoEvolve releases have no receipts and require a manual migration.
- Compare a conflicting file with its selected source in `adapters/manifest.json`,
  then merge the desired instructions yourself. Do not delete existing rules just
  to make the installer succeed. Future upgrades of manually merged files remain
  manual. A legacy `.clinerules` file must be migrated or merged before installing
  the directory-based Cline rule.
- All selected downloads are staged and checksum-validated before any instruction
  is changed. Each final file is replaced atomically; this is not a transaction
  across every file. Interrupted installs can be rerun. Transfer or checksum errors
  return nonzero and never leave a partial download at its final path.
- Checksums detect damaged distribution files; they are not a signature independent
  of the repository. Use a trusted commit for provenance.
- An install lock prevents simultaneous installers in one target. After a process
  is forcibly killed, confirm no installer is running before removing the stale
  `.autoevolve/install.lock` directory and abandoned staging directories.
- Review backups before restoring them. To uninstall, remove only the instruction
  files you installed (or the sections you manually merged). Keep goals and
  journals if useful. `.autoevolve/` is local installer state; exclude it from
  version control in your target project.

The installer reports file placement and conflicts, not successful agent activation.
Network, invalid-input, or filesystem errors return nonzero (normally 1); manual
integration conflicts return 2. Exit code 0 still requires the activation check.

## Outcomes and efficiency

There is **no measured token-saving or task-success claim** for this release.
Prompt overhead, model behavior, and host context loading vary. Compare verified
success, cost per success including failed attempts, elapsed time, and user
interventions using the [evaluation procedure](docs/evaluation.md) before claiming
a benefit.

## Development

`PROTOCOL.md` and `adapters/manifest.json` are canonical. Do not hand-edit generated
`AGENTS.md`, adapters, the compatibility guide, or `checksums.txt`.

```sh
python3 scripts/build_adapters.py
python3 scripts/build_adapters.py --check
python3 -m unittest discover -s tests -v
sh -n install.sh
```

With development tools installed:

```sh
python3 -m pip install -r requirements-dev.txt
ruff check scripts tests
ruff format --check scripts tests
mypy scripts tests
shellcheck install.sh
```

Python 3.10+ runs the generator and fixtures; it is not required by installed
projects. The suite uses `sh` on POSIX and available Windows PowerShell / `pwsh` on
Windows. It mocks network transfers and exercises real installer processes.
[CI](.github/workflows/ci.yml) covers Linux, macOS, Windows PowerShell 5.1, and
PowerShell 7. Live IDE activation and controlled agent-outcome trials are separate
from these checks.

## License

[MIT](LICENSE).
