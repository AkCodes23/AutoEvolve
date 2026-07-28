# AutoEvolve

**A mindset for AI coding agents, plus the tools that make it stick.**

Drop [`AGENTS.md`](AGENTS.md) into a repository. Your AI assistant reads it and works there in
small, verified steps: define an honest signal for "better", make the smallest correct change,
keep it only if it measurably improves things, journal it, simplify, repeat.

It is 38 lines. There is no runtime, no dependency, and nothing to build.

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
Across roughly 580 graded trials, **adding instruction text produced no detectable change in
agent behaviour**. Agents do not fail these steps out of ignorance; they anchor on the one symptom
in front of them. Rewording a rule cannot fix that. Removing the choice can.

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

Nothing here claims the mindset text improves model output. It was measured repeatedly and it
does not, which is why the scripts above exist. The benchmark harness and its results are not in
this repository; both are in git history at commit `9ac36c9` if you want to rerun them.

Nothing here claims the mindset text improves model output. It has been measured repeatedly and
it does not, which is the honest finding and the reason the mechanisms above exist.

## What is in this repo

```
AGENTS.md                     the mindset (the product; 38 lines)
adapters/                     four per-tool copies, GENERATED from AGENTS.md
templates/                    DIRECTION.md and JOURNAL.md to drop in a target repo
autoevolve.py                 install / init / check / setup / journal / hooks / loop
install.sh, install.ps1       the same install, without Python
scripts/
  callers.py, ruler.py, comments.py     the three mechanisms
  corpus_audit.py, ruler_audit.py       measure the two detectors on real corpora
  build_adapters.py, check.py           keep the adapters and invariants honest
  check_target.py, branch.py, run_quiet.py
  test_*.py                             72 tests, mutation-checked
docs/                         the loop as a checklist, one worked example, sources
skills/, commands/, .claude-plugin/     Claude Code plugin surface
```

## Contributing

Run `python3 scripts/check.py` before you commit; CI runs it on every push. If you change the
mindset, change `AGENTS.md` and run `python3 scripts/build_adapters.py`. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. See [`LICENSE`](LICENSE) and [`docs/SOURCES.md`](docs/SOURCES.md) for attribution.
