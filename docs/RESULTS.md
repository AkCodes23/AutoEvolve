# Results

> **What is and is not in this repository.** The benchmark harness that produced every number
> below has been removed, and the raw datasets were never published. Both are recoverable from
> git history at commit `9ac36c9`, which is where `evals/` was last intact.
>
> Say the cost out loud, because this file exists to be strict about exactly this: **you cannot
> reproduce these numbers from a fresh clone.** What you can still check is the method, the
> predictions that were registered before each run, and which of them failed. Everything stated
> here was measured against pre-registered predictions, with confidence intervals, and the
> failures are reported beside the successes.

## The finding that matters

**Instruction text does not measurably change agent behaviour.** Six experiments, roughly 650
graded trials across four models, plus a held-out task scored by six independent probes. No
ruleset, including this one and the two it draws on, produced a detectable improvement over a
plain control on any suite that could discriminate.

The failure mode is not ignorance of the rules. On the held-out task, **63 of 64 agents fixed the
one reported symptom and ignored five other real contract violations in the same 90-line file**,
each documented in that file's own docstrings. A deliberately maximal ruleset, with a mandatory
numbered procedure telling the agent to read every docstring and open every caller, failed its
own pre-registered test and captured about 4 percent of the available headroom.

**This is why [`scripts/`](../scripts/) contains mechanisms rather than more rules.** A script
that runs the lookup and puts the answer in front of the agent removes the choice. Rewording the
request does not. That is the single most useful thing this project measured, and it argues
against its own central artifact, which is why it is stated first.

A sixth replication arrived incidentally: across 146 comments authored by a model over 90 trials,
**43 percent narrated the diff** (`# Fix: use a parameterized query`) at effectively the same rate
under every ruleset tested. Control 13, AutoEvolve 12, ponytail 9, karpathy 8.

## What the numbers were

Balanced run, `llama-3.1-8b-instant`, 5 discriminating scenarios x 6 conditions x 3 trials, 90
trials, zero API and zero grader errors, grader revision `503e54e3af3b`.

| Condition | Graded checks | 95% CI | Tokens/turn |
| --- | ---: | :---: | ---: |
| control | 63.5% | [45, 81] | 0 |
| ponytail | 65.8% | [53, 78] | 294 |
| karpathy | 70.0% | [59, 81] | 349 |
| **AutoEvolve (condensed)** | **74.4%** | [59, 89] | 489 |
| AutoEvolve (long profile) | 69.4% | [57, 82] | 913 |

**Every interval spans zero. This is a direction, not a win, and must not be quoted as a ranking.**

Two decisions came out of it and both stand:

- **One profile, not two.** The condensed core scored higher at 47 percent fewer tokens, so the
  longer profile was retired rather than maintained beside it. `AGENTS.md` is now the only source
  and the adapters are generated from it.
- **A reworded variant was rejected by its own pre-registered rule:** +0.1 points for +53 tokens.
  Third independent time that rewording changed nothing.

The one unambiguous effect in that run was scope discipline: control 33 percent against 100
percent for every guided condition. **It did not replicate** in a later run, where control also
scored 100. Treat it as unresolved.

## The direct-code guardrail, 2026-07-28

45 trials, three arms, two of which differed by exactly one line of `AGENTS.md`. Zero errors, all
cells balanced, predictions registered first.

Shipped minus pre-guardrail: **-3.8 points, 95% CI [-11.9, +4.5]**. The pre-registered failure
condition was not triggered, so the line stays. State the bound honestly: the interval **cannot
exclude** a regression as large as the 10 points that would have reverted it. "No measurable
regression" is supported; "no regression" is not.

The registered positive control failed to replicate, so the per-scenario detail from that run is
recorded as noise rather than read as signal.

## Why earlier numbers were withdrawn

Everything this file said before 2026-07-27 was retracted rather than corrected, because for most
of it there was no correction available: the runner did not measure the quantity its table named.
The causes are worth keeping, because they are the failure modes to watch for in any re-run.

- **n=1 per cell.** A "pass rate" of 86 percent was six coin flips with no interval.
- **Half the trials were API errors**, and infrastructure failures had been dropped from the
  denominator instead of counted.
- **The multi-turn runner leaked the rubric**, injecting the grader's failing check names into the
  retry prompt, and its score could only move upward, so it could not report a regression.
- **The graders themselves were unsound.** One passed the untouched broken starter it existed to
  fail; another scored a still-vulnerable module full marks. All were rewritten to assert
  behaviour, each calibrated so the starter fails, a reference solution passes, and a plausible
  cheat fails.
- **Ceiling effects killed two whole suites.** Every condition scored 100 percent, so no trial
  count could have separated them. Check for this before spending anything.

## Method rules kept from all of it

- Register predictions before reading results, and report the ones that fail.
- A mean pooled over unbalanced cells is not a comparison.
- Run a power calculation first: binary metrics at n<=15 can only detect enormous effects.
- Graded per-check scores beat pass/fail; they cut the trials needed for the same power by six.
- Probes must be independent, or one noisy signal wears three costumes.
- Never pool scores from different grader revisions.
