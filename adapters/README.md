# Adapters

The canonical mindset is [`../AGENTS.md`](../AGENTS.md). These files are **thin
adapters**: each carries a condensed core and points back to `AGENTS.md` for the full
version. This is the *one source of truth, many thin adapters* pattern: keep the mindset
in one place and let each tool read it in whatever format that tool expects.

Copy the one your tool reads into **your** repository at the path shown:

| File | Copy to (in your repo) | Read by |
| --- | --- | --- |
| [`../AGENTS.md`](../AGENTS.md) | `AGENTS.md` (repo root) | Most agentic tools, including **Codex** and **Antigravity** (both read root `AGENTS.md` natively) |
| [`claude.md`](claude.md) | `CLAUDE.md` (repo root) | Claude Code (does not read `AGENTS.md`, so it gets its own file) |
| [`cursor.mdc`](cursor.mdc) | `.cursor/rules/autoevolve.mdc` | Cursor |
| [`windsurf.md`](windsurf.md) | `.windsurf/rules/autoevolve.md` | Windsurf |
| [`copilot-instructions.md`](copilot-instructions.md) | `.github/copilot-instructions.md` | GitHub Copilot |

If your tool reads a root `AGENTS.md` (Codex, Antigravity, and many others), you need no
adapter at all: just copy `AGENTS.md` in. If your tool isn't listed, use `AGENTS.md`
directly (it's plain Markdown any AI can read), or write a one-line adapter that says
*"Follow the operating mindset in `AGENTS.md`"* and pastes in the condensed core from any
file here.

The four inline adapters (`claude.md`, `cursor.mdc`, `windsurf.md`,
`copilot-instructions.md`) carry the **same** condensed core; only their frontmatter
differs. To keep them from drifting they are **generated** from one file: edit
[`../AGENTS.md`](../AGENTS.md), then run `python3 ../scripts/build_adapters.py` to re-stamp all
four. `python3 ../scripts/check.py` fails if they are ever out of date. The depth always
lives in `AGENTS.md`; these exist only because some tools need the guidance inline.
