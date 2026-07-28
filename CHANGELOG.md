# Changelog

All notable changes to AutoEvolve are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions aim to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pin a version when you install
so a moving `main` never changes the mindset under you.

## [Unreleased]
## [Unreleased]

### Added
- **`AGENTS.md` guardrail: write direct code.** Delete comments that restate the code, never
  commit commented-out code; a comment earns its place only by recording what the code cannot.
  Costs 65 tokens per turn (566 to 631). Untested: no claim it improves output.
- **`scripts/comments.py`** reports comment noise in changed files. `noise` is provable and can
  fail `--strict`; `candidate` is advisory. `--staged` implies `--baseline HEAD`, so adopting it
  in an existing repo cannot fail a commit over someone else's old comment.
- **`scripts/ruler.py`** reports what a change did to the tests that judge it, reading the signal
  `DIRECTION.md` declares. Report-only by design: nothing here is provable, so no gate.
- **`scripts/corpus_audit.py`, `scripts/ruler_audit.py`** reproduce the accuracy measurements
  below, with seeded samples so an audit can be checked rather than trusted.
- **`scripts/test_callers.py`, `test_comments.py`, `test_ruler.py`**, 65 tests, mutation-checked.
- `profile.py` records `grader_revision` on every row, so scores cannot be pooled across rulers.

### Fixed
- `scripts/callers.py` decoded git output with the machine's locale codec. One byte outside
  cp1252 killed subprocess's reader thread and returned `stdout=None` with **exit code 0**.
- `comments.py` died with `UnicodeEncodeError` partway through a report, losing every finding
  after it, on any comment outside the console codepage.
- Consecutive `#` lines are one comment; judging them separately caused every false positive
  found in a standard-library audit. Noise went 2.01 to 0.57 per KLOC.

### Removed
- **`evals/` and `docs/BENCHMARK.md`.** The benchmark harness, its 11 scenarios and its datasets
  are no longer part of this repository, which drops it from 11,788 to about 5,000 lines around a
  38-line product. Everything is recoverable from git history at `9ac36c9`.
- The cost is real and `docs/RESULTS.md` states it where the numbers appear: **those numbers can
  no longer be reproduced from a fresh clone.** What ships is the method, the pre-registered
  predictions, and which of them failed.

### Changed
- README 488 to 120 lines, CHANGELOG 416 to ~130, `docs/RESULTS.md` 372 to 100, two module
  docstrings halved, `docs/COMPATIBILITY.md` folded into `docs/INSTALL.md`. No capability removed.
- CI drops the eval steps and gains one: the mechanisms must come up clean under their own
  `comments.py --strict`.

### Measured
- Comment reporter: **0.00 to 0.57 noise per KLOC** across 8 corpora, 626k lines. Two hand audits
  of 30 random findings drove every detector.
- Ruler reporter: **7 percent (`urllib3`) and 14 percent (`click`)** of human test-touching
  commits raise `weakened`, against a bar of 25 set before measuring.
- Direct-code guardrail cost: **-3.8 points, 95% CI [-11.9, +4.5]** over 45 trials. No measurable
  regression; the interval cannot exclude one. A pre-registered positive control failed to
  replicate, so the per-scenario detail is recorded as noise. See `docs/RESULTS.md`.
- 43 percent of model-authored comments are diff-narration, at the same rate under every ruleset
  tested. A sixth replication that instruction text does not move behaviour.

### Removed (BREAKING)
- **The second profile.** `adapters/_core.md` is gone; `AGENTS.md` is the single source and the
  four adapters are generated from it. Measured: the condensed profile scored 74.4 percent at 489
  tokens against the longer one's 69.4 at 913. `--profile core|full` is removed from the
  installers and the CLI.

## [2.0.0] - 2026-07-24

Multi-mode mindset plugin, universal CLI, and an expanded evaluation suite.

### Added
- Universal cross-platform CLI (`autoevolve.py`) with `install`, `init`, `check`, `setup`,
  `journal`, `hooks`, and `loop`, across Windows, Linux, and macOS.
- Pre-flight repository checker (`scripts/check_target.py`).
- Population Branch Manager (`scripts/branch.py`) for quality-diversity niche branches
  (`evolve/fast`, `evolve/small`).
- Native Windows PowerShell installer (`install.ps1`) with dry-run, core profile, and idempotency.
- Competitor evaluation instruction sets (`evals/competitors/karpathy.md`,
  `evals/competitors/ponytail.md`).
- Expanded eval scenario suite: 7 scenarios (bugfix, optimize, feature, refactor, security, error
  handling, yagni).
- A deterministic regression suite for the profiler and the sandbox controls
  (`evals/test_profile.py`, run with `unittest`).

### Changed
- `scripts/run_quiet.py` runs commands with `subprocess.run(shell=False)`.
- `scripts/build_adapters.py` verifies all four generated IDE adapters against
  `adapters/_core.md` (`claude.md`, `copilot-instructions.md`, `cursor.mdc`, `windsurf.md`).
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
  `docs/INSTALL.md`. These describe and run toward a real agent benchmark; no held-out
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

[2.0.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/v2.0.0
[0.1.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/V0

> **Version note.** These entries are ahead of what is actually taggable. `.claude-plugin/plugin.json`
> declares `0.1.0`, the only git tag is `V0`, and both documented clone commands pin `V0`, so the
> `v2.0.0` link above does not resolve. Before publishing another release, make the manifest
> version, the git tag, and the install instructions agree: the README tells users to pin a
> version, and today no value satisfies that instruction.
