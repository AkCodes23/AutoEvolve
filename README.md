# AutoEvolve

**A mindset for AI coding agents, plus the tools that make it stick.**

Drop [`AGENTS.md`](AGENTS.md) into a repository. Your AI assistant reads it and works there in
small, verified steps: define an honest signal for "better", make the smallest correct change,
keep it only if it measurably improves things, journal it, simplify, repeat.

It is 36 lines. There is no runtime, no dependency, and nothing to build.

## Quick start

```bash
cp AGENTS.md /path/to/your/project/          # that is the whole install
```

Optionally, to also place tool-specific adapters (`CLAUDE.md`, `.cursor/rules/`,
`.windsurf/rules/`, `.github/copilot-instructions.md`) and scaffold the two working files:

```bash
python3 autoevolve.py setup --target /path/to/your/project
python3 autoevolve.py check --target /path/to/your/project
```

`AGENTS.md` is the single source of truth. The four files in [`adapters/`](adapters/) are
**generated** from it by `scripts/build_adapters.py`, so they cannot drift.

## The loop

Read [`AGENTS.md`](AGENTS.md) itself; it is shorter than any summary of it. In one line:

> Understand → define a frozen signal → baseline → smallest diff → verify cheapest check first →
> keep if better, else revert only what you touched → journal one line → simplify → repeat.

Two working files live in your repo: `DIRECTION.md` (human-owned: the objective, the signal, the
guardrails, the budget) and `JOURNAL.md` (append-only, one line per experiment).
[`docs/CHECKLIST.md`](docs/CHECKLIST.md) is the same loop as a tickable list, and
[`docs/EXAMPLE.md`](docs/EXAMPLE.md) walks one real bug through it.

## Mechanisms, not just rules

This is where AutoEvolve differs from the rulesets it draws on, and the difference is measured.
Across roughly 580 graded trials, **adding instruction text changed almost nothing about agent
behaviour**. The one exception is scope discipline, and every ruleset earns it equally (see
below), so it is not a reason to prefer this file over another. Treat the rest as unmoved: on
that first suite, five of seven scenarios scored 100 percent for every condition, and a
ceiling cannot show a difference no matter how many trials run against it, which is why
scenarios 08 to 11 were added later. Agents do not fail these steps out of ignorance; they
anchor on the one symptom in front of them. Rewording a rule rarely fixes that. Removing the
choice can.

So the loop's three most-skipped steps each have a script that does the work and puts the answer
in front of you. All are standard library only, all report rather than rewrite, and all take
`--root` so you can run them from here against another repository.

| Step | Script | What it does |
| --- | --- | --- |
| Before editing | [`scripts/callers.py`](scripts/callers.py) | Lists every call site of every symbol you changed |
| Before verifying | [`scripts/ruler.py`](scripts/ruler.py) | Reports what your change did to the tests that judge it |
| While simplifying | [`scripts/comments.py`](scripts/comments.py) | Reports comments that restate the code, and commented-out code |

```bash
python3 scripts/callers.py                    # symbols in your uncommitted changes
python3 scripts/ruler.py                      # did you move the goalposts?
python3 scripts/comments.py --staged --strict # for a pre-commit hook
```

Their accuracy is measured against code nobody here wrote, because calibrating a detector on your
own habits proves nothing. `comments.py` reports **0.00 to 0.57 noise findings per KLOC** across
eight corpora and 626k lines; `ruler.py` flags **7 to 14 percent** of human test-touching commits,
against a bar of 25 percent set before measuring. Reproduce both with
[`scripts/corpus_audit.py`](scripts/corpus_audit.py) and
[`scripts/ruler_audit.py`](scripts/ruler_audit.py), each of which prints a seeded sample so an
audit can be checked rather than trusted.

## What it is built from

An independent synthesis of four sources, each contributing one layer. Full attribution in
[`docs/SOURCES.md`](docs/SOURCES.md).

| Source | Contribution |
| --- | --- |
| **AlphaEvolve** (DeepMind) | Ground every change in execution. Small diffs, not rewrites. Keep a diverse population, not one champion. |
| **autoresearch** (Karpathy) | The change → verify → keep-or-revert loop, with git as the experiment store and a frozen, human-owned signal. |
| **ponytail** (DietrichGebert) | The minimalism ladder, deletion over addition, and this repo's one-source-plus-thin-adapters shape. |
| **Karpathy's LLM guidelines** | Verification is the bottleneck. Distrust your evals. Keep a human on the autonomy slider. |

## Honesty about what is proven

Nothing here claims the mindset text reliably improves model output. It was measured repeatedly
and, with the single exception below, it does not, which is why the scripts above exist. The
benchmark harness and its results are not in this repository; both are in git history at commit
`9ac36c9` if you want to rerun them.

The one place any ruleset helped is worth stating precisely, because it is easy to misread as a
win for this one. On a scope-discipline scenario (do the task asked, leave adjacent code alone)
the unguided model scored 33 percent and **ponytail, Karpathy's guidelines and AutoEvolve each
scored 100 percent**. That is an any-preamble effect, shared equally by all three, not an
advantage of this file. Across the other four discriminating scenarios every ruleset landed at
or below the unguided baseline: control 71 percent, AutoEvolve 68, Karpathy 63, ponytail 57.

So the defensible claim is narrow: among rulesets, this one costs the least. It is not that it
adds value over an empty prompt. Those numbers come from one model (`llama-3.1-8b-instant`) at
three trials per cell, on the five of eleven scenarios where every condition completed every
cell; the other six had no balanced cells and pooling them would credit a condition for the
model that happened to run it. Read the whole section as directional, not settled.

## What is in this repo

```
AGENTS.md                     the mindset (the product; 36 lines)
adapters/                     four per-tool copies, GENERATED from AGENTS.md
templates/                    DIRECTION.md and JOURNAL.md to drop in a target repo
autoevolve.py                 install / init / check / setup / journal / hooks / loop
install.sh, install.ps1       the same install, without Python
scripts/
  callers.py, ruler.py, comments.py     the three mechanisms
  corpus_audit.py, ruler_audit.py       measure the two detectors on real corpora
  build_adapters.py, check.py           keep the adapters and invariants honest
  check_target.py, branch.py, run_quiet.py
  test_*.py                             80 tests, mutation-checked
docs/                         the loop as a checklist, one worked example, sources
skills/, commands/, .claude-plugin/     Claude Code plugin surface
```

## Contributing

Change the mindset in `AGENTS.md` and nowhere else, then run
`python3 scripts/build_adapters.py` to regenerate the adapters. Run `python3 scripts/check.py`
and `python3 -m unittest discover -s scripts -p "test_*.py"` before you commit. Keep `AGENTS.md`
and `docs/` tool-neutral; tool names belong in `adapters/`.

## License

MIT. See [`LICENSE`](LICENSE) and [`docs/SOURCES.md`](docs/SOURCES.md) for attribution.
