# AutoEvolve

**A mindset plugin for AI coding agents.** Drop it into any repository. When an AI
assistant reads it, it knows how to work there: *what* to do, *how* to do it, the full
scope of *what all* to do, and *why*.

AutoEvolve is **not a program you run.** There is no engine, no dependency, nothing to
install into a runtime. It is a small set of Markdown instructions that carry one coherent
way of working, distilled from four systems for autonomous, self-improving engineering. You
copy it into your repo; your existing AI tools read it and follow its discipline.

---

## Quick Start (30 seconds)

1. **Copy [`AGENTS.md`](AGENTS.md) into your target project root.**
2. **Your AI tools (Claude Code, Cursor, Windsurf, Copilot, etc.) will read it automatically.**

No dependencies, no runtime installation, and no build step required.

Optional: Run `python autoevolve.py install --target /path/to/project` to automatically copy IDE-specific adapter files into `.cursor/rules/`, `.windsurfrules`, or `.github/copilot-instructions.md`.

---

## Contents

- [The problem it solves](#the-problem-it-solves)
- [The four sources](#the-four-sources)
- [The core loop](#the-core-loop)
- [The minimalism ladder](#the-minimalism-ladder)
- [The keep rule](#the-keep-rule)
- [Guardrails: never be lazy about these](#guardrails-never-be-lazy-about-these)
- [Autonomy and intensity](#autonomy-and-intensity)
- [Reconciling the tensions](#reconciling-the-tensions)
- [Conventions](#conventions)
- [How to use it in your repo](#how-to-use-it-in-your-repo)
- [What is in this repo](#what-is-in-this-repo)
- [Attribution and license](#attribution-and-license)

---

## The problem it solves

Left unguided, an AI coding agent tends to write a large, plausible-looking change, declare
it done, and move on. Nothing forced it to prove the change actually works, nothing stopped
it from adding needless complexity, and nothing recorded what it tried so the next session
could build on it. Over a long task these failures compound into confident, unverified, over-
engineered code.

AutoEvolve replaces that with a disciplined loop: make the *smallest* change that could
work, *prove* it against a real signal, *keep* it only if it is genuinely better, *write
down* what you learned, and repeat. It turns an agent from a code generator into something
closer to a tireless, honest researcher who never regresses the codebase and always leaves a
trail a human can trust.

## The four sources

AutoEvolve is an independent synthesis. Each source contributes a distinct layer. Full
attribution and further reading is in [`docs/SOURCES.md`](docs/SOURCES.md).

| Source | What AutoEvolve takes from it |
| --- | --- |
| **AlphaEvolve** (Google DeepMind), an evolutionary coding agent | Ground every change in execution and an automatic check, so hallucinated "progress" cannot survive. Edit in small diffs, not rewrites. Keep a *diverse population* of good solutions (not one champion) to escape local optima. Learn from the last run's real error. Evaluate cheap checks first. |
| **autoresearch** (Andrej Karpathy), a recipe that turns a coding agent into an unattended researcher | The tight *change to verify to keep-or-revert* loop, with git as the experiment store (HEAD = best-known state). A human-owned, frozen, un-gameable signal. An append-only journal. One change per experiment. "Don't stop mid-loop; when out of ideas, think harder." |
| **ponytail** (DietrichGebert), a "laziest senior dev" minimalism ruleset | The decision ladder ("the best code is the code you never wrote"). Deletion over addition. Gate correctness and safety before rewarding brevity. Mark deliberate corner-cuts. Its distribution shape, *one source of truth plus thin per-tool adapters*, is the shape of this repo. |
| **Karpathy's general guidelines** for building with LLMs | Verification, not generation, is the real bottleneck, so shrink verification time and fear big diffs. Distrust your evals. Treat context as scarce memory and write durable notes. Keep a human on the autonomy slider: "build the Iron Man suit, not the runaway robot." |

The insight of combining them: AlphaEvolve supplies the *engine* (grounded, diff-based,
diverse iteration), autoresearch supplies the *discipline* (a frozen signal and a
keep/revert loop you can run unattended), ponytail supplies the *taste* (do less, and do it
correctly), and Karpathy's guidelines supply the *engineering judgment* (fast feedback,
honest evals, human-in-the-loop). None of them alone is the whole picture; together they are
a complete way of working.

## The core loop

Everything in the plugin elaborates this one cycle. Run it on every non-trivial task.

```
         +--------------------------------------------------------------+
         |  0. UNDERSTAND the problem (read the code, reproduce the bug) |
         +--------------------------------------------------------------+
                                     |
   +---------------------------------v-------------------------------------+
   |  1. DEFINE THE SIGNAL. What does "better" mean here? A number, a      |
   |     red-to-green test, or an acceptance check. Keep the ruler         |
   |     separate from the thing being measured.                          |
   +---------------------------------v-------------------------------------+
                                     |
   +---------------------------------v-------------+
   |  2. BASELINE. Measure the current state and   |
   |     commit a clean checkpoint to return to.   |<------------------------+
   +---------------------------------v-------------+                          |
                                     |                                        |
   +---------------------------------v-------------+                          |
   |  3. SMALLEST CORRECT CHANGE (walk the ladder).|                          |
   |     One hypothesis, one diff.                 |                          |
   +---------------------------------v-------------+                          |
                                     |                                        |
   +---------------------------------v-------------+                          |
   |  4. VERIFY. Does it run? Is it correct? Only  |                          |
   |     then: is it smaller/faster/cleaner?       |                          |
   +---------------------------------v-------------+                          |
                                     |                                        |
                 +-------------------+-------------------+                    |
        meets the keep rule?                          no                     |
                 |                                      |                     |
   +-------------v-------------+          +-------------v--------------+       |
   |  5a. KEEP. Commit it.     |          |  5b. REVERT. Discard it;   |       |
   |      The new best (HEAD).  |          |      keep the lesson.      |       |
   +-------------v-------------+          +-------------v--------------+       |
                 +-------------------+------------------+                     |
                                     |                                        |
   +---------------------------------v-------------+                          |
   |  6. JOURNAL one line.                         |                          |
   |  7. SIMPLIFY (same result with less?).        |--------------------------+
   |  8. REPEAT. Stay diverse. Don't stop; escalate.
   +-----------------------------------------------+
```

Step by step:

0. **Understand first.** Read the surrounding code and reproduce the problem before you
   touch anything. The ladder runs *after* understanding, never instead of it.
1. **Define the signal.** Decide how you will tell "better" before editing. A signal does
   not have to be a number. It can be a **number** (a benchmark, a timing), a **binary** (a
   test that goes red to green, a lint or type check that passes), or an **acceptance
   check** you confirm by running or re-reading (the specific things the output must do).
   Not every task has a number, but every task has a "better" you can pin down. Keep the
   ruler separate from the code it measures so the code can never quietly rewrite its own
   grader.
2. **Baseline.** Record where you are starting from, and commit a clean checkpoint. HEAD is
   now a known-good state you can always return to.
3. **Make the smallest correct change.** Walk the ladder. One hypothesis, one small diff,
   so the result is attributable to that change and nothing else.
4. **Verify, cheapest check first.** Does it even run? Then, is it correct? Then, only after
   correctness and safety pass, is it smaller, faster, or cleaner? Read the *actual* output,
   not your expectation of it. If a number is noisy, take the median of a few runs.
5. **Keep or revert.** Apply the keep rule below. Keepers get committed and become the new
   best; everything else is reverted, and the lesson is kept. A reverted experiment is a
   success too: it ruled an option out.
6. **Journal one line.** *commit, signal, keep/revert, what changed, why.* This is your
   external memory across long sessions and hand-offs.
7. **Simplify.** Can you reach the same result with less code? Deleting is a win.
8. **Repeat, and do not stop when stuck.** Out of ideas is not a stopping point: re-read the
   code and references, combine near-misses, or try a radical alternative. Stop only at a
   real terminal state or a genuine decision for a human.

**Git is the experiment store.** HEAD is always your single best-known solution; a commit
is a kept experiment; a targeted revert of only the experiment's known files throws one away
cleanly. For experiments that may create many files, use a dedicated worktree. Never use
bulk cleanup to discard files you did not create. Because each experiment is isolated and
inspectable, you can be bold without risking unrelated user work.

## The minimalism ladder

Before writing any code, stop at the first rung that holds:

1. **Does this need to be built at all?** (YAGNI. The best code is the code you never wrote.)
2. **Does it already exist in this codebase?** Reuse the helper, util, or pattern.
3. **Does the standard library already do this?** Use it.
4. **Does a native platform or language feature cover it?** Use it.
5. **Does an already-installed dependency solve it?** Use it; do not add a new one.
6. **Can this be one line?** Make it one line.
7. **Only then:** write the minimum code that works.

The ladder runs *after* you understand the problem, not instead of it. The smallest change
in the *wrong* place is not lazy, it is a second bug. Deletion over addition, boring over
clever, fewest files, shortest working diff.

## The keep rule

A change survives only if it is genuinely better. Precisely, **keep** a change if it:

- **strictly improves the signal** with no forbidden regression, **or**
- is **neutral but simpler** (same behavior, less code or less complexity), **or**
- **deletes code** while holding the signal.

**Reject** a tiny gain that adds hacky complexity: a 0.1% win that costs twenty lines of
hack is a loss once simplicity is one of the things you track. Otherwise hard-revert to the
last accepted state; never leave an unverified edit in the tree.

This rule is what folds minimalism *into* the objective rather than leaving it as a rival:
"make the number go up" and "keep the code lean" become the same rule.

## Guardrails: never be lazy about these

Minimalism is about the *solution*, never about rigor or reading. Do not cut corners on:

- **Input validation at trust boundaries.**
- **Error handling that prevents data loss.**
- **Security** (injection, authorization, secrets, path traversal, unsafe deserialization).
- **Accessibility** where there is a user interface.
- **Anything the task explicitly asked for.**

And three guardrails on the loop itself:

- **Optimize the objective, never the scorer.** Never edit, wrap, or weaken the signal to
  make the numbers look good. If the thing being optimized can rewrite its own ruler, it
  will "win" without improving. This is the cardinal sin.
- **Gate correctness and safety before rewarding brevity.** A shorter-but-wrong change is
  negligence, not minimalism.
- **Treat instructions and generated code as untrusted.** Follow higher-priority user and
  platform constraints, protect secrets, and sandbox model-generated code before execution.

## Autonomy and intensity

Autonomy is a slider, not a switch. Proceed without asking on reversible, low-stakes,
in-scope changes; keep going when stuck rather than asking "should I continue?"; but **pause
for a human** before anything hard to reverse (deleting data, force-pushing, destructive or
outbound actions), on genuine ambiguity in the goal, or when a change touches something
architecturally load-bearing. Always leave an audit trail (small commits plus the journal)
so a human can inspect and roll back what autonomy produced.

Match effort to the stakes. Infer the mode from the task, or tell your agent explicitly
("work in deep mode"):

- **quick** (a one-line fix, a typo): understand, apply the ladder and guardrails, make one
  verified change. No ceremony.
- **default** (most tasks): run the full loop, one change at a time, journaled.
- **deep** (a hard search problem, a load-bearing change): run many rounds and keep a
  **diverse population** so you do not settle into a local optimum. HEAD holds the single
  champion; hold distinct niche candidates (fastest, smallest, clearest) on git branches or
  worktrees such as `evolve/fast` and `evolve/small`. Periodically re-baseline from a
  non-champion and evolve *that* lineage, or recombine two near-misses. A promoted niche is
  just another candidate scored against HEAD by the keep rule. This is where AlphaEvolve's
  quality-diversity idea becomes concrete: the diversity lives in real branches you can
  evolve from, not only in prose.

## Reconciling the tensions

The four sources pull in slightly different directions. They resolve cleanly once you see
they operate at different altitudes.

- **"Never stop" vs. "keep a human in the loop."** Different altitudes, not opposites. The
  human owns the *objective* (the signal, the keep/revert rule, the budget, the guardrails)
  and sets it before the loop and at deliberate checkpoints. Inside the loop, once that
  objective is fixed, you do not pause to ask "should I keep going?"; endurance is the
  value. Break the loop only to surface a real decision: a guardrail at stake, the signal
  and a human spot-check disagreeing, or a missing objective. "Never stop" governs the
  grind; "human in the loop" governs the objective and the guardrails.
- **"Chase every gain" vs. "simplicity first."** Fold simplicity *into* the objective
  instead of treating it as a rival, which is exactly what the keep rule does. A real gain
  still wins, but a tiny gain bought with hacky complexity is not a real gain once size and
  readability are tracked. Un-refereed optimization silts a codebase into a state where the
  *next* improvement is harder.
- **"One champion" vs. "a diverse population."** Resolve by scope. The git tree keeps
  exactly one champion (HEAD), which keeps the repo coherent and every result attributable.
  Diversity lives in branches, worktrees, and the journal (the best idea per niche, with its
  score). You explore a diverse population of *ideas* while committing a single coherent
  *artifact*.

## Conventions

A repo that adopts this mindset uses a few small conventions:

- **`DIRECTION.md`** (human-owned, read-only): the objective, the signal (and where the
  read-only scorer lives), the guardrails, and the budget. The agent optimizes *toward* it
  and never edits it. Copy-paste starter: [`templates/DIRECTION.md`](templates/DIRECTION.md).
- **`JOURNAL.md`** (append-only): one line per experiment, *commit, signal, keep/revert,
  what changed, why.* Re-read it at the start of a session. Copy-paste starter:
  [`templates/JOURNAL.md`](templates/JOURNAL.md).
- **`evolve:` comments** mark a deliberate corner-cut with its ceiling and upgrade path,
  e.g. `# evolve: O(n^2) scan, fine < 10k rows; use a hash index above that`.
- **Small commits** with clear messages are the experiment log; the current state is the
  best-known solution.

See [`docs/EXAMPLE.md`](docs/EXAMPLE.md) for one real task walked end to end through the
loop, and [`docs/CHECKLIST.md`](docs/CHECKLIST.md) for the whole thing as a tickable list.

## How to use it in your repo

Pick whichever your AI tools already read; you can use more than one.

The safest path is to download and review a release checkout, then let the installer detect
your tools. It installs the context-efficient core by default, never overwrites existing
files, and reports when a manual merge is required:

```bash
git clone --depth 1 --branch V0 https://github.com/AkCodes23/AutoEvolve.git
cd AutoEvolve
./install.sh --target /path/to/your/repo --dry-run
./install.sh --target /path/to/your/repo
```

Use `--profile full` only when you deliberately want the longer operating manual in every
agent turn; benchmark it against the core first.

Or copy the operating core in by hand after reviewing the release:

```bash
# Universal cross-platform CLI installation into any target project:
python AutoEvolve/autoevolve.py install --target /path/to/your/repo --profile core
python AutoEvolve/autoevolve.py init --target /path/to/your/repo
python AutoEvolve/autoevolve.py check --target /path/to/your/repo

# Or manually copy AGENTS.md:
cp /path/to/AutoEvolve/AGENTS.md /path/to/your/repo/AGENTS.md
```

Full details, including the per-tool adapters and how to pin a version, are in
[`docs/INSTALL.md`](docs/INSTALL.md).

**Claude Code users** can install it as a plugin instead of copying files:

```
/plugin marketplace add AkCodes23/AutoEvolve
/plugin install autoevolve@autoevolve
```

**Confirm it is active:** ask your agent "what is your operating loop?" It should describe
the understand, signal, baseline, smallest-change, verify, keep-or-revert cycle.

1. **The universal way, `AGENTS.md`.** Copy [`AGENTS.md`](AGENTS.md) into your repo root.
   Many AI coding tools read a root `AGENTS.md` automatically; point the rest at it.
2. **As tool-native rules.** Copy the thin adapter for your tool from
   [`adapters/`](adapters/): Claude Code, Cursor, Windsurf, or GitHub Copilot. Each is a
   condensed core that points back at `AGENTS.md`. (Codex and Antigravity read a root
   `AGENTS.md` natively, so they need no adapter.)
3. **As a loadable skill.** Copy [`skills/autoevolve/SKILL.md`](skills/autoevolve/SKILL.md)
   into your agent's skills directory so it loads on demand.
4. **As commands.** The templates in [`commands/`](commands/) are concrete, invocable
   actions: `baseline`, `evolve`, `simplify`, `review`, `journal`.

Then tell your assistant to work "the AutoEvolve way," or run `baseline` then `evolve` on a
task, and keep a `JOURNAL.md` as you go.

## What is in this repo

```
AGENTS.md                     the lean operating core (read/loaded every turn)
README.md                     this file: the full explanation
`autoevolve.py`                 universal cross-platform CLI tool (install, init, check)
`install.sh`                    POSIX one-command installer (auto-detects tools)
`install.ps1`                   Windows PowerShell native installer
`scripts/check_target.py`       target repository readiness checker (0-100% score)
skills/autoevolve/SKILL.md    the mindset as a loadable agent skill
commands/                     invocable prompt templates
  baseline.md                 define the signal and record the baseline
  evolve.md                   run the loop on a task
  simplify.md                 apply the ladder to shrink code
  review.md                   an over-engineering review
  journal.md                  the experiment-log format
adapters/                     thin per-tool rule files, all pointing at AGENTS.md
  _core.md                    the single source the four inline adapters are generated from
  claude.md                   Claude Code (copy to CLAUDE.md)
  cursor.mdc                  Cursor
  windsurf.md                 Windsurf
  copilot-instructions.md     GitHub Copilot
templates/                    copy-paste starters: DIRECTION.md, JOURNAL.md
docs/
  PRINCIPLES.md               why each rule exists, in depth
  EXAMPLE.md                  one task walked end to end through the loop
  CHECKLIST.md                the operating checklist, standalone
  INSTALL.md                  how to add this to your repo
  BENCHMARK.md                agent benchmark protocol (experimental, Proof-tier: not yet run)
  COMPATIBILITY.md            tool matrix (install surfaces verified; behavior not yet tested)
  SOURCES.md                  attribution and further reading
evals/                        runnable scenarios for measuring the mindset's effect
  run.py                      grade a scenario: python3 evals/run.py 01_bugfix
  profile.py                  sandboxed prompt A/B (control vs core vs full)
  agent_benchmark.py          sandboxed benchmark runner (experimental, Proof-tier)
  sandbox.py                  fail-closed Docker execution boundary for generated code
.claude-plugin/               Claude Code plugin + marketplace manifests
scripts/
  check.py                    the self-check (no em dashes, links, tool-neutral core, adapters, JSON)
  build_adapters.py           regenerate the adapters from adapters/_core.md
.github/workflows/check.yml   runs the self-check on every push and pull request
CONTRIBUTING.md   CHANGELOG.md   LICENSE
```

The design follows ponytail's *one source of truth, many thin adapters*: `AGENTS.md` is the
source of truth. The four inline adapters carry a condensed copy for tools that read rules
inline, and they are **generated** from `adapters/_core.md` by `scripts/build_adapters.py`
so they cannot drift. When the mindset changes, change `AGENTS.md` (and `_core.md` if the
condensed core moves).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). In short: `AGENTS.md` is the single source of
truth; the adapters are generated from `adapters/_core.md` (run `python3
scripts/build_adapters.py` after editing it); and before opening a pull request, run the
self-check that CI also runs:

```bash
python3 scripts/check.py
```

It confirms there are no em dashes, that the mindset core stays tool-neutral (tool names
belong in `adapters/`), that every internal link resolves, and that the adapters are up to
date with `adapters/_core.md`. To measure the mindset's effect on a real task, run the
scenarios in [`evals/`](evals/): `python3 evals/run.py --all`. Versions are tracked in
[`CHANGELOG.md`](CHANGELOG.md); pin one when you install so a moving `main` never changes
the mindset under you.

## Attribution and license

AutoEvolve is an independent synthesis of publicly described ideas. It is not affiliated
with or endorsed by AlphaEvolve, autoresearch, ponytail, or their authors. See
[`docs/SOURCES.md`](docs/SOURCES.md) for references.
