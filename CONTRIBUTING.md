# Contributing

Thanks for improving AutoEvolve. It is Markdown, not software, so contributing is quick.

## The one rule: single source of truth

`AGENTS.md` is the canonical mindset. Everything else points back to it. In particular, the
four inline adapters (`adapters/claude.md`, `cursor.mdc`, `windsurf.md`,
`copilot-instructions.md`) are **generated** from one file:

- Edit the mindset in **`AGENTS.md`** (never the adapters directly: they are generated).
- Regenerate: `python3 scripts/build_adapters.py`
- There is ONE profile. If you change the mindset, edit `AGENTS.md`, then run the generator to
  match if the change touches the condensed core.

## Before you open a PR

Run the self-check. It is the repo's own signal, the same one CI runs:

```bash
python3 scripts/check.py
```

It confirms there are no em dashes, that the mindset core stays tool-neutral (tool names
belong in `adapters/`), that every internal link resolves, and that the adapters are
up to date with `AGENTS.md`.

## Conventions

- **No em dashes.** Use commas, colons, or parentheses.
- **Keep the core tool-neutral.** `AGENTS.md`, `skills/`, `commands/`, and the conceptual
  docs must not name a specific tool; put tool-specific paths in `adapters/` and `docs/INSTALL.md`.
- **Practice what it preaches.** Small diffs, walk the ladder, keep changes verifiable.

## Flow

Branch, open a pull request against `main`, and let CI go green. Squash-merge keeps history
tidy. That's it.
