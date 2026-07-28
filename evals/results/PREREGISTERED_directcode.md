# Pre-registered predictions: does the direct-code guardrail cost anything?

Written and committed BEFORE the run's results were read.

## The question, and why it is the only one worth API calls

The direct-code guardrail added 65 tokens to `AGENTS.md` (566 to 631). Its *intended* effect is
unmeasurable on this suite, and that was established for free before spending anything:

- The 90 stored outputs of the 2026-07-27 run contain **2 comment-noise findings in 90 files**,
  and 47 of 90 files have no comments at all. The tasks are patches to files of 3 to 75 lines and
  `BASE_INSTRUCTION` ends with "Do not explain". There is no noise here to reduce, so no trial
  count could show a reduction. Building a comment-authorship probe instead would repeat the
  ceiling-effect mistake that voided two earlier benchmarks in this repository.
- What the stored outputs *do* show is that models author about 1.5 comments per file and that
  **43 percent of them are diff-narration** (`# Fix: use a parameterized query`), produced at
  effectively the same rate by every ruleset: control 13, autoevolve 12, ponytail 9, core_v2 9,
  karpathy 8. That is a sixth independent replication of this repository's central finding, and
  it is the argument for the mechanism rather than for the sentence.

So the guardrail's benefit is not what this run tests. This run tests its **cost**. The suite can
detect whether extra context makes the model worse, which is the question `profile.py` was built
for: "if `autoevolve` does worse than `control`, the context is making the model dumber."

## Design

`llama-3.1-8b-instant`, the 5 discriminating scenarios (`05_security`, `08_reuse`,
`09_collateral`, `10_scope`, `11_complexity`), 3 arms, 3 trials per cell, 45 trials.

| Arm | File | Approx. tokens |
| --- | --- | --- |
| `control` | none | 0 |
| `autoevolve_prev` | `variants/agents_pre_directcode.md` (commit `3518dca`) | 566 |
| `autoevolve` | `AGENTS.md` as shipped | 631 |

`autoevolve_prev` and `autoevolve` differ by **exactly one line**, verified by diff. Everything
else about the two prompts is byte-identical, so any difference between those two arms is
attributable to the guardrail and nothing else.

## Power ceiling, stated before the run

This cannot resolve a small difference and is not being asked to. The 2026-07-27 run at this
exact size (5 scenarios, 3 trials) produced intervals spanning zero for a **10.9 point** gap. So
a null here excludes a large regression and nothing more. That is still worth the calls: the case
for keeping the guardrail is "it probably does not hurt", and this converts that from an
assumption into a bounded claim.

## Predictions

1. **`autoevolve` and `autoevolve_prev` land within a few points of each other**, with an
   interval spanning zero. The added line says nothing about any behaviour these five graders
   measure.
2. **`autoevolve_prev` does not beat `autoevolve` by more than 10 points.** This is the
   pre-registered failure condition. If it does, the guardrail is charging 65 tokens per turn for
   a measurable regression and should be reverted, whatever it does for comment quality.
3. **`10_scope` stays at or near 100 percent for both guided arms and well below it for
   control.** This was the one unambiguous effect of the previous run (control 33 percent, every
   guided condition 100 percent) and is the closest thing this suite has to a positive control.
   If it does not replicate, doubt the run before reading anything else in it.
4. **No arm wins overall by a margin whose interval excludes zero**, consistent with every
   predecessor.

## What will not be claimed afterwards

That the guardrail improves anything. It is not being tested for that here, no measurement in
this repository has ever shown instruction text improving output, and the honest statement after
a null result is that 65 tokens bought no measurable regression.
