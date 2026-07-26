# Changelog

All notable changes to AutoEvolve are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions aim to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pin a version when you install
so a moving `main` never changes the mindset under you.

## [Unreleased]

## [2.0.0] - 2026-07-24

Production Release 2.0: Comprehensive multi-mode mindset plugin, universal CLI, production hardening, and expanded empirical evaluation suite.

### Added
- Universal cross-platform CLI (`autoevolve.py`) supporting `install`, `init`, and `check` commands across Windows, Linux, and macOS.
- Pre-flight repository checker (`scripts/check_target.py`) that audits target repos and reports 0-100% readiness score.
- Population Branch Manager (`scripts/branch.py`) for managing quality-diversity niche branches (`evolve/fast`, `evolve/small`).
- Native Windows PowerShell Installer (`install.ps1`) with dry-run, core profile installation, and idempotency checks.
- Pre-commit configuration (`.pre-commit-config.yaml`) for automated pre-commit CI invariant and adapter drift validation.
- Automated release packaging script (`scripts/release.py`).
- Authentic competitor evaluation instruction sets (`evals/competitors/karpathy.md` and `evals/competitors/ponytail.md`).
- Expanded eval scenario suite (6 scenarios: bugfix, optimize, feature, refactor, security, error handling).
- 31-test pytest unit test suite covering shell injection prevention, path traversal defense, unicode console encoding, and CLI timeouts.

### Changed
- Rebuilt `AGENTS.md` operating core with Tiered Ceremony (`quick`, `default`, `deep` modes), Step 0 exploration, rolling journal compaction, and 3-commit hypothesis windows.
- Hardened `scripts/run_quiet.py` using `subprocess.run(shell=False)` with list parsing to eliminate shell injection vulnerabilities.
- Updated `scripts/build_adapters.py` with SHA256 checksum verification across all 4 generated IDE adapters (`claude.md`, `copilot-instructions.md`, `cursor.mdc`, `windsurf.md`).

[2.0.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/v2.0.0

### Changed
- Installer no longer runs a remote script. `install.sh` runs only from a reviewed release
  checkout (`--target`, `--dry-run`, `--profile core|full`), defaults to the compact core
  profile, and never overwrites an existing file.
- The revert step no longer recommends `git clean`. Destructive tree cleanup was removed from
  `AGENTS.md` and the docs; a dirty tree you did not create is left untouched.
- Installer reporting is accurate. A repeat install or a hand-merged file now reports "already
  installed" and exits 0, and when adapters are written while `AGENTS.md` still needs a manual
  merge, it says the adapters are already active instead of claiming nothing was activated.

### Added
- `evals/sandbox.py`, a fail-closed Docker boundary (no network, read-only mount, dropped
  capabilities, no environment forwarding) for grading model-generated code. `evals/profile.py`
  refuses to execute model output unless a digest-pinned sandbox image is configured.
- Experimental Proof-tier scaffolding: `evals/agent_benchmark.py`, `docs/BENCHMARK.md`, and
  `docs/COMPATIBILITY.md`. These describe and run toward a real agent benchmark; no held-out
  suite has been run and no tool behavior has been verified yet.

## [0.1.0] - 2026-07-19

Initial public release: a drop-in mindset plugin for AI coding agents.

### Added
- `AGENTS.md`, the lean operating core (the loop, the ladder, the keep rule, guardrails,
  autonomy and intensity, conventions).
- `README.md`, the full explanation, and `docs/` (`PRINCIPLES`, `EXAMPLE`, `CHECKLIST`,
  `INSTALL`, `SOURCES`).
- The mindset as a loadable skill (`skills/autoevolve/SKILL.md`) and as invocable commands
  (`commands/`: `baseline`, `evolve`, `simplify`, `review`, `journal`).
- Tool adapters: Claude Code, Cursor, Windsurf, and GitHub Copilot. Codex and Antigravity
  read root `AGENTS.md` natively.
- A Claude Code plugin install path: the repo is its own plugin marketplace
  (`.claude-plugin/`), so users can `/plugin marketplace add AkCodes23/AutoEvolve` then
  `/plugin install autoevolve@autoevolve` instead of copying files.
- One source of truth for the adapters (`adapters/_core.md`) plus a generator
  (`scripts/build_adapters.py`) so they cannot drift.
- A one-command installer (`install.sh`) that auto-detects your tools, and starter
  templates (`templates/DIRECTION.md`, `templates/JOURNAL.md`).
- A runnable eval harness (`evals/run.py`) and a context profiler (`evals/profile.py`) for
  measuring the mindset's real effect on a model, including its token cost per turn.
- A self-check (`scripts/check.py`) and CI that enforce the repo's own invariants (no em
  dashes, tool-neutral core, links resolve, adapters generated, plugin JSON valid) and keep
  the eval harness wired.

[0.1.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/V0
