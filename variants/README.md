# Candidate mindset revisions

## Verdict log

**`core_v2` (2026-07-27): REJECTED, not adopted.** It replaced the guardrail "Context verification
before editing" with "name its callers and what each one expects; fix the contract where it is
broken, not at the one call site that reported the symptom". The hypothesis was that an
operational instruction would beat an abstract one, specifically on `09_collateral`.

Measured on the balanced 90-trial dataset: **+0.1 points overall** (95% CI -15 to +12) for
**+53 tokens on every turn**, and on `09_collateral`, the scenario it was written for, it moved
the score from 56% to 56%. It also scored WORSE than `core` on `11_complexity` (71% vs 100%).

The decision rule was written before the run: a neutral result means revert. The file is kept so
the next person does not re-run the same experiment, which is the whole point of a journal.

This is the third independent time this project has measured that rewording the instruction text
does not move behaviour. The lever that did move it in the same run was not wording at all: on
`10_scope`, every guided condition scored 100% against control's 33%, so the presence of
guidance mattered where its phrasing did not.


Files here are NOT shipped and NOT installed. They exist so a proposed change to the mindset can
be measured against the current one before it is adopted:

```bash
# The profiler that ran this lives in git history at 9ac36c9.
python3 evals/profile.py --condition core_v2=variants/core_v2.md \
  --conditions control,core,core_v2 --runs 3
```

Keep the revision only if it beats `core` on the graded score without costing disproportionately
more tokens, and revert it otherwise. That is the loop this project describes, applied to the
project's own instruction text, with the eval suite as the frozen signal.

A revision that wins only on the scenarios it was written against has not been validated, it has
been fitted. Check it against the whole suite, and prefer wording that states a general
engineering action over wording that names a scenario's specifics.
