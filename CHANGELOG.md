# Changelog

All notable changes to AutoEvolve are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions aim to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pin a version when you install
so a moving `main` never changes the mindset under you.

## [0.1.0] - 2026-07-18

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
- One source of truth for the adapters (`adapters/_core.md`) plus a generator
  (`scripts/build_adapters.py`) so they cannot drift.
- A self-check (`scripts/check.py`) and CI that enforce the repo's own invariants.
- A one-command installer (`install.sh`) that auto-detects your tools.
- Starter templates (`templates/DIRECTION.md`, `templates/JOURNAL.md`).
- An eval methodology and scenarios (`evals/`) for measuring the mindset's effect.

[0.1.0]: https://github.com/AkCodes23/AutoEvolve/releases/tag/v0.1.0
