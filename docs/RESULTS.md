# Results

> **Status.** This file now holds one measured comparison, with its raw rows committed beside it
> and its predictions registered before the results were read. It reports a **direction, not a
> win**: the leading condition's confidence interval spans zero, and the file says so in the place
> a reader would otherwise quote.
>
> Everything this file said before 2026-07-27 is **RETRACTED**. It published a table headed
> "Empirical Benchmark Results" while [`BENCHMARK.md`](BENCHMARK.md) simultaneously stated that no
> held-out suite had been run and that "nothing here should be cited as measured performance". The
> old numbers were not reproducible and several were produced by instruments since shown to be
> broken. They are removed rather than corrected, because for most of them there is no correction:
> the runner did not measure the quantity the table named. The next section explains each one, so
> that anyone who saw those figures elsewhere can see exactly why they are gone.

## Why the old numbers were withdrawn

Each of these was verified against the raw data and the code that produced it.

**The single-turn table was n=1 per cell.** `evals/results/70b_xml_benchmark.jsonl` holds 35
rows: 7 scenarios x 5 conditions x **one** trial. A "pass rate" of 86% (6/7) is six coin flips,
not a rate. No confidence interval was reported, and none of the differences between conditions
survives any interval you could draw around one observation per cell.

**The other dataset was mostly failed API calls.** `evals/results/70b_1run.jsonl` holds 30 rows
of which **12 are `api_error` and 5 are `grader_error`**: only 13 trials produced a verdict at
all. `BENCHMARK.md` explicitly requires that infrastructure failures stay in the denominator.

**Neither dataset shipped.** Both files are matched by `.gitignore`, and neither is tracked, so
a fresh clone received the conclusions and none of the evidence.

**The multi-turn half measured scorer leakage.** The 86% multi-turn figure came from
`evals/agent_loop_sim.py`, which at the time injected the grader's failing **check names**
verbatim into the retry prompt: the model was handed the rubric, including the exact adversarial
inputs and the required API. That runner also had no `--output`, so no raw data exists for the
multi-turn table at all. Two further structural problems mean a re-run would not have rescued
it: `best_score` only ever moves upward, so the runner cannot report a regression (which is the
one thing keep-or-revert exists to prevent), and it recorded no single-turn arm, so the
"33-50% single-turn" comparison figure cannot be derived from the tool it was attributed to.

**The graders themselves were not sound.** Every number above was produced against scenario
graders that a later review found defective. Most consequentially, `02_optimize` passed the
untouched O(n^2) starter it exists to fail, `05_security` scored a module still vulnerable in
all four advertised ways at 5/5, and `06_errorhandling` gave full marks to a module whose every
function returned `None`. A comparison run against a ruler that cannot detect failure measures
nothing, so those scores are void rather than merely imprecise.

**The arithmetic did not check out.** The claim that the core delivers its benefit "at less than
25% of the token context cost" of the full profile contradicted the same table's own figures
(721 vs 1,092 prompt tokens, which is 66%).

## Measured, 2026-07-27: head to head on the discriminating suite

Raw rows: [`../evals/results/`](../evals/results/), grader revision `503e54e3af3b`. Predictions
were written before the results were read, in
[`../evals/results/PREREGISTERED.md`](../evals/results/PREREGISTERED.md). Read that alongside this.

Frozen before the run: 5 scenarios (`05_security`, `08_reuse`, `09_collateral`, `10_scope`,
`11_complexity`), 6 conditions, 3 trials per cell, temperature 0.2, seed 20260727,
`max_tokens` 1600, calls paced 22 to 26 seconds apart, randomized trial order, graded in the
Docker sandbox on a digest-pinned image. The other six scenarios were deliberately excluded: they
measure 100 percent for every condition, so trials there spend quota without carrying information.

**Zero API failures and zero grader failures across all 165 trials.**

`llama-3.1-8b-instant` completed all 90 of its trials. The two `openai/gpt-oss` models reached
37 and 38 of 90 before their throughput collapsed and the run was stopped, so their cells are
unevenly filled. The headline below therefore uses **only the balanced 90-trial dataset**. That is
not a cosmetic choice: in the pooled view, `core` appeared to score 29 percent on `05_security`
against control's 71 percent, which turned out to be an artifact of which model happened to
complete which cell. `core` had no `05_security` rows from either strong model. A per-scenario mean
that pools across models is not a comparison.

### Balanced: llama-3.1-8b-instant, 5 scenarios x 6 conditions x 3 trials, 0 errors

The `core` and `full` labels below are what the committed datasets carry. They were the two
AutoEvolve profiles at the time of the run. `full` was retired as a result of it, so the current
harness has a single `autoevolve` arm and there is nothing left named `core` or `full`.

| Condition | Graded checks | 95% CI | Tokens/turn |
| --- | ---: | :---: | ---: |
| control | 63.5% | [45, 81] | 0 |
| ponytail | 65.8% | [53, 78] | 294 |
| full | 69.4% | [57, 82] | 913 |
| karpathy | 70.0% | [59, 81] | 349 |
| **core** | **74.4%** | [59, 89] | 489 |
| core_v2 | 74.6% | [62, 87] | 542 |

Paired by scenario against control: core **+10.9** pts (CI -6 to +39), core_v2 +11.0
(-14 to +42), karpathy +6.5 (-16 to +39), full +5.9 (-20 to +39), ponytail +2.3 (-20 to +36).

**`core` ranks first and beats both competitor rulesets, but every interval spans zero over five
cells.** This is a direction, not a result. Do not cite it as a win. It is the first time this
project's instrument has been able to show a direction at all, which is the actual news.

### Per scenario, same balanced dataset

| Scenario | control | karpathy | ponytail | core | core_v2 | full |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 05_security | 38% | 42% | 38% | 29% | 46% | 38% |
| 08_reuse | 88% | 62% | 62% | 88% | 100% | 88% |
| 09_collateral | 59% | 56% | 48% | 56% | 56% | 56% |
| **10_scope** | **33%** | **100%** | **100%** | **100%** | **100%** | **100%** |
| 11_complexity | 100% | 90% | 81% | 100% | 71% | 67% |

### What the pre-registered predictions got right and wrong

- **`10_scope`: confirmed, and it is the only unambiguous effect in the run.** Control scored 33
  percent; every guided condition scored 100. A 67-point gap on three trials per cell. Karpathy was
  predicted to lead here and did, tied with the others. Guidance plainly changes behaviour on
  "do exactly what was asked and leave the adjacent code alone".
- **`08_reuse`: half right.** Karpathy was predicted to score like control because it never mentions
  reuse; it scored 62 against control's 88, which is worse than predicted. But ponytail, predicted to
  lead, also scored 62. The prediction that a ladder rung would show up as a ponytail advantage
  failed.
- **`09_collateral`: failed.** Ponytail was predicted to lead and scored lowest (48%). Control scored
  highest (59%). No condition helped.
- **`11_complexity`: failed.** `core` and `full` were predicted to lead because AutoEvolve is now the
  only ruleset that mentions complexity. Control scored 100 percent, tying `core`, and `full` scored
  worst at 67. The complexity guardrail did not earn anything measurable here: this model already
  optimises both axes when asked to. The guardrail stays because the guidance gap was real, but the
  claim "it improves outcomes" is not supported.
- **The falsifier**: `core` (74.4) does beat both `karpathy` (70.0) and `ponytail` (65.8). `full`
  (69.4) does not beat `karpathy`. So the synthesis clears its own bar in the condensed profile
  only, and only nominally.

### The work axis, which separates better than the score

Tokens are an input price and checks passed are an output score. Neither measures the work, and
the work is the claim: smallest correct diff, deletion over addition. Churn is computed from the
stored source on every trial, so this needed no extra model calls and is reproducible from the
committed rows.

| Condition | Graded | Churn (lines) | Removed | Gained over starter | **Gain / 10 lines** |
| --- | ---: | ---: | ---: | ---: | ---: |
| control | 63.5% | 15.5 | 6.8 | 30.4% | **0.60** |
| ponytail | 65.8% | 16.3 | 6.5 | 33.5% | 0.93 |
| full | 69.4% | 15.4 | 7.1 | 37.3% | 0.92 |
| karpathy | 70.0% | **13.5** | 6.3 | 36.1% | 0.97 |
| core | 74.4% | 15.0 | 6.7 | 43.0% | **1.01** |
| core_v2 | 74.6% | 13.9 | 6.2 | 40.8% | 1.00 |

Two things here that the score alone does not show:

**Control is the least efficient worker by a wide margin.** 0.60 checks gained per 10 lines
changed against roughly 0.92 to 1.01 for every guided condition. Unguided output is not merely
lower-scoring, it is lower-scoring *per line it disturbed*. That gap (about 40 percent less
efficient than `core`) is proportionally larger than the gap in the graded score, so the work axis
sees something the score compresses.

**Karpathy demonstrably writes the smallest diffs**: churn **-1.9 lines against control, 95% CI
[-3.3, -0.5]**. That interval excludes zero, and it is the first one in this project's history to
do so on any axis. It is also exactly what karpathy's section 3 claims ("Touch only what you must",
"don't improve adjacent code"), so the instrument agreed with the ruleset's own stated strength
rather than with a favoured conclusion.

Note what this does NOT show: `core` does not win the churn comparison (-0.5 lines, CI -1.2 to
+0.1). It wins on gain per line, by scoring higher at similar churn. Those are different claims and
the table keeps them separate.

Credit is given only for improvement **over the starter**, deliberately. Measured against the raw
score, a submission that changed nothing at all would rank as the most efficient possible answer,
since the starters already pass some checks for free.

### Two decisions this run settled, and one consequence

1. **`core` stays as the only profile; `full` is retired.** 74.4 percent at 489 tokens beats 69.4
   percent at 913. The longer profile cost 87 percent more context on every turn and scored lower,
   so it is gone rather than maintained alongside the winner. There is now one file, `AGENTS.md`,
   and the per-tool adapters are generated from it.
2. **`core_v2` is rejected.** See [`../variants/README.md`](../variants/README.md): +0.1 points for
   +53 tokens, and 56 percent to 56 percent on the scenario it was written for.

**What shipped is not byte-identical to what was measured, and that matters.** The measured winner
was the 1959-character condensed core (about 489 tokens). The surviving `AGENTS.md` is 2264
characters (about 566 tokens), because the retired profile held the only definition of `DIRECTION.md`
and `JOURNAL.md`, which `commands/`, `templates/` and the CLI all depend on, so that block was
carried across. That is **+77 tokens of untested increment**. It is a conventions block rather than
a behavioural rule, so the risk is low, but the honest statement is that the shipped file has not
itself been through the comparison. Re-running the suite against it is the obvious next measurement.


### The honest limits of this run

Five cells is not enough for any interval to exclude zero, and one model is not a population. The
right next run is three or more models to completion on these five scenarios, which needs either
paid rate limits or patience: a shared token allowance across models made parallel execution
self-defeating, and pacing three models under one bucket is slower than running them in sequence.
Nothing here should be quoted as a ranking.

## Superseded: 2026-07-27 demonstration run against the 7-scenario suite

Raw rows: [`../evals/results/llama-3.1-8b-instant.g8a4a8f4a1d2c.jsonl`](../evals/results/llama-3.1-8b-instant.g8a4a8f4a1d2c.jsonl)
(70 rows, every one carrying `sandboxed`, `sandbox_image`, `temperature`, `max_tokens`, `seed`,
`prompt_sha256`, and the graded source).

> Kept for the record. Its grader revision is `8a4a8f4a1d2c`, so its scores are NOT poolable with
> the run above, and the suite it used has since been extended. Its value now is the ceiling
> finding, not its condition table.

Frozen before the run: `llama-3.1-8b-instant`, all 7 scenarios, all 5 conditions, 2 trials per
cell, temperature 0.2, seed 20260726, `max_tokens` 2048, randomized trial order, graded in the
Docker sandbox on a digest-pinned image. Grader revision `8a4a8f4a1d2c` (sha256 of every
`grade.py`). Zero API failures and zero grader failures, so the denominator is the full 70.

**This run is a demonstration that the repaired instrument works end to end. It is not a powered
comparison and no condition is ranked.** One small model at 2 trials per cell cannot separate
conditions, and the point of running it was to produce real rows against a ruler that is no
longer broken.

| Condition | Graded checks | 95% CI | Strict pass | Approx tokens/turn |
| --- | ---: | :---: | ---: | ---: |
| control | 87.8% | [75.5, 97.8] | 64% | 0 |
| karpathy | 88.9% | [76.6, 98.9] | 71% | 349 |
| ponytail | 88.0% | [76.6, 97.1] | 64% | 294 |
| core | 87.4% | [73.9, 98.4] | 64% | 443 |
| full | 88.1% | [76.8, 97.3] | 64% | 827 |

Differences blocked on (model, scenario) cells, bootstrapped: karpathy +1.1 pts
[+0.0, +3.3], ponytail +0.2 [-4.5, +4.2], core -0.3 [-3.2, +2.7], full +0.3 [-1.6, +2.7],
all against control. Every interval contains zero. Against `core` rather than control, no
competitor separates either. All five conditions sit inside a 1.5-point band.

### The finding that matters more than the table

Per-scenario graded means expose a ceiling:

| Scenario | control | karpathy | ponytail | core | full |
| --- | ---: | ---: | ---: | ---: | ---: |
| 01_bugfix | 100% | 100% | 100% | 100% | 100% |
| 02_optimize | 100% | 100% | 100% | 100% | 100% |
| 03_feature | 92% | 100% | 100% | 88% | 88% |
| 04_refactor | 100% | 100% | 88% | 100% | 100% |
| 05_security | 38% | 38% | 44% | 31% | 44% |
| 06_errorhandling | 85% | 85% | 85% | 92% | 85% |
| 07_yagni | 100% | 100% | 100% | 100% | 100% |

Three scenarios are at 100% for every condition and two more are within a check of it. Only
`05_security` discriminates at all. **Adding trials cannot fix this.** A scenario where every
condition scores 100% contributes no information about the conditions no matter how many times
it is run, so most of this suite is currently measuring nothing about prompts.

The graders are calibrated so the broken STARTER fails, which is the right calibration for
"did the agent fix it". It is the wrong calibration for "did the instruction text change the
outcome", because a competent model one-shots most of these tasks from the task description
alone. Headroom against the starter is not headroom against a model.

This is consistent with the prior rounds recorded above and with roughly 580 earlier trials: the
honest reading is not "the mindset does not work" but "single-turn scenarios of this difficulty
cannot detect whether it works". Measuring the instruction text at all needs tasks where a
competent model fails without guidance: multi-file changes, a contract documented somewhere the
model must choose to look, a case where the correct action is to stop and ask, and a canary that
punishes collateral damage. `05_security` is the only current scenario in that class, and it is
the only one with a usable gradient.

## What is still true

The **context cost** of each condition is deterministic, reproducible with no API key, and was
never in question. Regenerate it at any time:

```bash
python3 evals/profile.py --tokens
```

Measured on the current files (characters, and an approximate token count at chars/4). Because
these move whenever the instruction files are edited, regenerate rather than trusting the table:

| Condition | Source | Characters | Approx tokens | Lines |
| --- | --- | ---: | ---: | ---: |
| control | (no instruction text) | 0 | 0 | 0 |
| ponytail | `evals/competitors/ponytail.md` | 1176 | 294 | 22 |
| karpathy | `evals/competitors/karpathy.md` | 1398 | 349 | 33 |
| autoevolve | `AGENTS.md` (the only profile) | 2264 | 566 | 37 |

There is one profile, so there is no step to describe. When two existed, the measured winner was
the 34-line condensed one at 489 tokens and the retired profile was 56 lines at 913. Earlier drafts
of this file described the gap as "the extra ~125 lines" and `AGENTS.md` as "~150 lines", neither of
which was ever true of any committed version.

This is the cost half of the question. It says what you pay on every turn, and nothing about
what you get for it.

## Publishing a number here again

The bar is set by [`BENCHMARK.md`](BENCHMARK.md), and the short version is: report the
instrument alongside the result.

1. Grade in the sandbox. Rows now carry `sandboxed` and `sandbox_image` so a reader can tell
   which interpreter produced a verdict.
2. Report the graded per-check score, not only strict all-or-nothing pass. A scenario with 15
   checks carries far more signal per trial than one bit, and the harness now records
   `checks_passed`/`checks_total` for exactly this reason.
3. Report an interval, and enough trials to justify it. Prefer blocking on
   (model, scenario) cells, since model strength and scenario difficulty dominate the variance.
4. Ship the raw JSON Lines in the same commit as the claim, and keep API and grader failures in
   the denominator.
5. Say plainly which claim is being tested. `profile.py` is a blind single-turn prompt ablation.
   It is not evidence about the multi-step agent workflow the mindset actually describes, and it
   should never be labelled as though it were.
