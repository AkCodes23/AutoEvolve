# AutoEvolve

**A mindset plugin for AI coding agents.** Drop it into any repository; when an AI
assistant reads it, it knows how to work there — *what* to do, *how*, the full scope of
*what all* to do, and *why*.

It is **not a program you run.** There is no engine, no dependency, nothing to install
into a runtime. It is a small set of instructions that carries one coherent way of
working, distilled from four systems for autonomous, self-improving engineering:

| Source | What AutoEvolve takes from it |
| --- | --- |
| An **evolutionary coding-agent** approach | Ground every change in a real measured result; edit in small diffs; keep a *diverse* set of good solutions, not one champion. |
| An **autonomous-research recipe** | The tight *change → verify → keep-or-revert* loop, a frozen honest signal, an append-only journal, and "don't stop — think harder." |
| A **minimalist "laziest senior dev"** ruleset | The decision ladder; the best code is the code you never wrote; gate correctness before rewarding brevity. |
| **General guidelines for building with LLMs** | Small diffs, fast verification, distrust your evals, context as scarce memory, a human on the autonomy slider. |

> The one thing to read is **[`AGENTS.md`](AGENTS.md)** — the canonical operating
> mindset. Everything else in this repo is a thin adapter that points an AI back to it.

---

## Use it in your repo

Pick whichever your AI tools already read (see [`docs/INSTALL.md`](docs/INSTALL.md) for
details):

1. **The universal way — `AGENTS.md`.** Copy [`AGENTS.md`](AGENTS.md) into your repo
   root (or link to it). Many AI coding tools read `AGENTS.md` automatically; the rest
   can be pointed at it.
2. **As a skill.** Copy [`skills/autoevolve/SKILL.md`](skills/autoevolve/SKILL.md) into
   your agent's skills directory so it loads on demand.
3. **As tool-native rules.** Copy the thin adapter for your tool from
   [`adapters/`](adapters/) (Cursor, Windsurf, Copilot, …). Each one is a short pointer
   to `AGENTS.md` plus the condensed core, following the *one source of truth, many thin
   adapters* pattern.
4. **As commands.** The prompt templates in [`commands/`](commands/) are concrete,
   invocable actions — `evolve`, `baseline`, `simplify`, `review`, `journal`.

Nothing here is tool-specific magic; it's plain Markdown an AI reads and follows.

## The mindset in one screen

```
0. UNDERSTAND the problem first.
1. DEFINE the signal — a fast, honest, hard-to-game way to tell "better."
2. BASELINE it; commit a clean checkpoint.
3. PROPOSE the smallest correct change (walk the ladder).
4. VERIFY — smoke test, then correctness, then (only then) size/speed.
5. KEEP if better (or neutral-but-simpler, or a deletion) & correct, else REVERT — keep the lesson.
6. RECORD one line in the journal.
7. SIMPLIFY — same result with less? Deleting is a win.
8. REPEAT — stay diverse, don't stop when stuck (escalate), pause for humans on the
   irreversible or ambiguous.
```

**The ladder** (run it before writing any code):

> 1. Does this need to exist at all? (YAGNI) → 2. Already in this codebase? Reuse it. →
> 3. Standard library? Use it. → 4. Native platform feature? Use it. → 5. An
> already-installed dependency? Use it. → 6. Can it be one line? → 7. Only then: the
> minimum code that works.

## What's in here

```
AGENTS.md                     the canonical operating mindset (read this)
skills/autoevolve/SKILL.md    the mindset as a loadable agent skill
commands/                     invocable prompt templates (evolve, baseline, simplify, review, journal)
adapters/                     thin per-tool rule files (Cursor, Windsurf, Copilot) → AGENTS.md
docs/
  PRINCIPLES.md               the "why", in depth
  CHECKLIST.md                the operating checklist, standalone
  INSTALL.md                  how to add this to your repo
  SOURCES.md                  attribution and further reading
LICENSE
```

## License

MIT — see [LICENSE](LICENSE). AutoEvolve is an independent synthesis of publicly
described ideas; it is not affiliated with or endorsed by any of the sources above.
