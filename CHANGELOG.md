# Changelog

All notable changes to AutoEvolve are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions aim to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pin a version when you install
so a moving `main` never changes the mindset under you.

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

[0.1.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/v0.1.0
