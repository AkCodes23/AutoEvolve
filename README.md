# AutoEvolve

> **Evolve the code, don't just write it: small steps, each verified.**

AutoEvolve is a minimal, zero-dependency mindset prompt for AI coding assistants.

It synthesizes the core principles of **DeepMind AlphaEvolve** (grounded verification), **Karpathy's autoresearch** (keep-or-revert loop), and **Dietrich Gebert's Ponytail** (YAGNI minimalism ladder) into a single 36-line drop-in ruleset.

---

## The Core Loop

```
0. Understand scope and reproduce
1. Freeze the signal (define the test/metric before editing; never edit the scorer)
2. Baseline HEAD
3. Smallest diff (change only what the task needs)
4. Verify cheapest first (compiles -> correct -> speed and memory)
5. Keep if better, simpler, or a deletion; else revert cleanly from HEAD
6. Journal one line (commit, signal, decision, what changed)
7. Simplify relentlessly
8. Repeat (stop after 10 loops for a human check-in)
```

---

## The Minimalism Ladder

Stop at the first rung that holds:
1. **Not at all (YAGNI)** — Speculative need = skip it.
2. **Reuse what is here** — Helper or pattern already in the codebase $\rightarrow$ reuse it.
3. **Stdlib** — Standard library does it $\rightarrow$ use it.
4. **Platform feature** — Native language or runtime feature covers it $\rightarrow$ use it.
5. **Installed dependency** — Already-installed package solves it $\rightarrow$ use it. Never add a new dependency for what a few lines can do.
6. **One line** — Can it be one line? One line.
7. **Minimum code** — Only then, write the minimum working code.

---

## Guardrails

- **Surgical**: Change only what the task needs. Leave adjacent code, formatting, and comments alone.
- **Contract-aware**: Know the callers before you edit; fix the shared contract, not just the one call site that failed.
- **Trust boundaries**: Validate at trust boundaries with no silent coercion. Categorize errors (client/server/dependency), time out all I/O.
- **Direct code**: No comments that restate the code, no commented-out code. Comment only what code cannot say: a measured result, a rejected alternative, a caveat.
- **Context frugality**: Run test suites in quiet mode (`pytest -q`), inspect the summary and failing lines.
- **Signal integrity**: Optimize the objective, never the scorer. Correct before brief.
- **Tree safety**: Never bulk-discard a dirty tree; work you did not create may be in it.

---

## Quick Setup (1-Click Drop-In)

| Tool / IDE | Adapter File | Target Location in Your Repository |
|:---|:---|:---|
| **Claude Code / AGENTS.md** | [`AGENTS.md`](./AGENTS.md) | `AGENTS.md` (or `CLAUDE.md`) |
| **Cursor** | [`adapters/cursor.mdc`](./adapters/cursor.mdc) | `.cursor/rules/autoevolve.mdc` |
| **Windsurf** | [`adapters/windsurf.md`](./adapters/windsurf.md) | `.windsurfrules` |
| **GitHub Copilot** | [`adapters/copilot-instructions.md`](./adapters/copilot-instructions.md) | `.github/copilot-instructions.md` |
| **Cline / Roo Code** | [`adapters/cline.md`](./adapters/cline.md) | `.clinerules` |
| **Aider** | [`adapters/aider.md`](./adapters/aider.md) | `CONVENTIONS.md` (or `aider --read adapters/aider.md`) |
| **Continue.dev** | [`adapters/continue.md`](./adapters/continue.md) | `.continue/prompts/autoevolve.prompt` |
| **Gemini / Antigravity** | [`adapters/gemini.md`](./adapters/gemini.md) | `GEMINI.md` |
| **Zed AI** | [`adapters/zed.md`](./adapters/zed.md) | `.zed/rules.md` |
| **JetBrains AI / Junie** | [`adapters/jetbrains.md`](./adapters/jetbrains.md) | `.jetbrains/ai-instructions.md` |
| **Sourcegraph Cody** | [`adapters/cody.md`](./adapters/cody.md) | `.cody/instructions.md` |
| **OpenHands / SWE-Agent** | [`adapters/openhands.md`](./adapters/openhands.md) | `.openhands/instructions.md` |

---

## Conventions

- **[`DIRECTION.md`](./DIRECTION.md)** (Human-owned): Defines the objective, the frozen signal, guardrails, and iteration budget.
- **[`JOURNAL.md`](./JOURNAL.md)** (Append-only): One-line log of each experiment: commit hash, signal result, keep/revert decision, and rationale.

---

## License

[MIT](./LICENSE)
