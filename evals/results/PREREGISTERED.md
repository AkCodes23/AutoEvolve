# Pre-registered predictions for the 2026-07-27 extended-suite run

> Left exactly as written, including the `core` / `full` / `core_v2` arm names. Those were the arms
> at the time. The run retired `full` and rejected `core_v2`, so the current harness has one
> `autoevolve` arm; editing this file to match would defeat the point of registering it.

Written and committed BEFORE the run's results were read. The point is to make the outcome
falsifiable: a prediction recorded afterwards is a story, not a test. Each row names the
condition expected to lead and the reason, drawn from what each ruleset actually says.

Run: 4 models x 11 scenarios x 6 conditions x 3 trials, seed 20260727, grader revision recorded
in `grader_revision.txt` alongside the dataset.

## Per-scenario predictions

| Scenario | Expected to lead | Why |
| --- | --- | --- |
| `08_reuse` | ponytail, core, full | Reuse-before-writing is ladder rung 2 in ponytail and AutoEvolve. Karpathy never mentions it, so karpathy should score like control. |
| `09_collateral` | ponytail, then core/full | Ponytail states it almost verbatim ("one guard in the shared function is a smaller diff than a guard in every caller"). AutoEvolve's "confirm callers before editing" is more general. Karpathy's "touch only what you must" is arguably in tension with the scored answer. |
| `10_scope` | karpathy | Karpathy sections 2 and 3 are the most specific statement of this discipline in any of the three. AutoEvolve is expected to LOSE this one. |
| `11_complexity` | core, full | After this session's change, AutoEvolve is the only ruleset that mentions time or space complexity at all. If instruction text moves behaviour anywhere, it should move it here. |
| `01` to `07` | no separation | Five of seven were at 100 percent for every condition in the previous run. They are regression tests, not discriminators. |

## Head-to-head prediction

No condition wins overall by a margin its interval excludes zero for. The prior on this is
strong: roughly 650 graded trials across this suite's predecessors found no detectable effect of
instruction text, and three earlier "effects" reversed on replication. The extended suite raises
the ceiling, so a real effect now has room to show; it does not guarantee one exists.

## The candidate revision

`core_v2` differs from `core` in exactly one guardrail: "Context verification before editing"
becomes "name its callers and what each one expects, fix the contract where it is broken".
Prediction: `core_v2` beats `core` on `09_collateral` specifically, and is neutral elsewhere. It
costs 53 more tokens per turn, so a neutral result means revert, not keep.

## What would falsify the project's central claim

AutoEvolve describes itself as a synthesis of these sources. If `core` and `full` do not beat
BOTH `karpathy` and `ponytail` on the suite as a whole, the synthesis is not buying anything a
reader could not get from a shorter, cheaper source file, and the honest response is to say so
here rather than to look for a subgroup where it wins.
