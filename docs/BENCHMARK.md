# Benchmark protocol

> Status: experimental (Proof-release tier). This is the protocol the agent benchmark will
> follow, not results already obtained. `evals/agent_benchmark.py` is a runner scaffold, and
> no held-out suite has been run yet. Nothing here should be cited as measured performance.

AutoEvolve must be measured as an agent workflow, not as a one-shot code-completion prompt.
The profiler is a compact prompt ablation. The agent benchmark measures the product claim:
does the guidance help an agent make safer, verified repository changes?

## Preconditions

- Use held-out tasks that were not used to write the prompt or examples.
- Run every trial in a disposable repository copy.
- Grade agent-produced code only in the Docker sandbox described in `evals/README.md`.
- Freeze task definitions, graders, model versions, tool versions, temperatures, and budgets
  before starting a comparison.

## Conditions

Run the same task under four randomized conditions:

1. `control`: normal agent instructions, no AutoEvolve file.
2. `karpathy`: the Karpathy guidelines, `evals/competitors/karpathy.md`.
3. `ponytail`: the ponytail minimalism ruleset, `evals/competitors/ponytail.md`.
4. `autoevolve`: the mindset, `AGENTS.md`. There is one profile; `core` and `full` were
   separate arms until a measured run retired the longer one.

Both competitor arms are required, not optional. AutoEvolve describes itself as a synthesis of
these sources, so beating an unguided control is not the claim: beating either source alone is.
A run that omits them cannot support the project's central claim.

The runner must expose the same task, repository snapshot, tools, timeout, and token budget
to every condition. Randomize trial order with a recorded seed so provider drift does not
systematically favor a condition.

## Validate the instrument before the run

A comparison is only as good as its grader, and this repository has already shipped graders that
could not detect failure. Before any run whose numbers you intend to publish, confirm for each
scenario that:

- the unmodified starter FAILS, and by a margin (that gap is the headroom being measured);
- a reference correct solution reaches full marks (otherwise the grader has a false-failure bug
  and is penalizing the behavior you are asking for);
- at least one plausible cheat FAILS, and one stylistically different correct solution PASSES;
- no check asserts on source text rather than behavior, treats any exception as proof of
  validation, infers success from something being absent, or depends on wall-clock timing or the
  host operating system.

Record which grader revision produced the numbers. Scores from different grader revisions are not
comparable and must not be pooled.

## Changing the mindset, and proving the change was an improvement

The mindset text is the product, so a change to it is a hypothesis and must be treated like one.
The harness supports this directly, without editing the shipped files:

```bash
cp AGENTS.md variants/candidate.md            # then make ONE change to the copy
python3 evals/profile.py --condition core_v2=variants/core_v2.md \
  --conditions control,karpathy,ponytail,core,core_v2 --runs 3
```

Keep the revision only if it beats `autoevolve` on the graded score by a margin its interval supports,
and does not cost disproportionately more tokens (`--tokens` prices every arm, including yours).
Revert it otherwise. That is this project's own loop, with the eval suite as the frozen signal.

Two failure modes to guard against, both of which look like success:

- **Fitting the scenarios.** A revision that names a scenario's specifics will win on that
  scenario and generalize to nothing. Prefer wording that states a general engineering action.
  Check the revision against the whole suite, not the scenario that motivated it.
- **Editing the ruler instead of the text.** If a revision only wins after a grader is adjusted,
  the grader change must stand on its own merits, tested against a cheat and a correct solution
  before any comparison is run. Optimizing the objective is the point; optimizing the scorer is
  the cardinal sin this project names.

Measure before rewording. Across roughly 650 graded trials on this suite's predecessors, no
change to the instruction TEXT produced a detectable effect, while the measured failure mode was
behavioural: agents anchor on the one symptom named in the task. A mechanism that performs the
step (a command that lists the callers of a changed symbol, run before editing) removes the
choice that wording only requests. Prefer the mechanism when one is available.

## Measure work, not price

Token cost is an input price. Checks passed is an output score. Neither is a measure of the work
performed, and the work is the whole claim: this project does not promise better code so much as
smaller, verified, better-justified changes. A benchmark that reports only tokens and pass rates
cannot see that, and will happily rate a condition that rewrote a 70-line file identically to one
that changed two lines.

Three of these are already recorded on every trial by `evals/profile.py`, computed from the
produced source with no extra model calls: `churn`, `lines_added`, `lines_removed`,
`starter_lines_kept`. `--regrade` backfills them onto older datasets. Use them: on the first run
that reported them, the work axis separated the conditions more cleanly than the score did, and
produced this project's first confidence interval that excluded zero.

### What a tool-using agent should additionally report

`evals/profile.py` is single-turn, so the work it can see is limited to the diff. A real
tool-using agent run through `evals/agent_benchmark.py` can report the rest, and these are the
metrics that would actually test the loop rather than the prose:

| Signal | Why it is the work, not the price |
| --- | --- |
| Tool calls, split by kind (read / edit / run) | Reads before edits is the "confirm callers before editing" claim, made countable |
| Whether a test or build was executed at all, and how many times | Step 4 of the loop. An agent that never ran the signal did not verify, whatever it claimed |
| Turns to first green, and turns after green | Work after the task is done is churn by another name |
| Reverts performed | Keep-or-revert is the central mechanism. If no run ever reverts, the mechanism is decorative |
| Files touched outside the declared scope | Collateral damage, which `09_collateral` measures statically and an agent run can measure directly |
| Journal lines written | The claim is an auditable trail; either it exists or it does not |

Report cost per unit of work alongside cost per success: an agent that reaches the same result in
half the tool calls is the better agent even at equal token spend, and an agent that reaches it
with a smaller diff is better still.

## Budgeting a run

Two limits bind, and they bind differently:

- **Requests per day**, which caps the total size of a run. Count it as
  `scenarios x conditions x runs` per model.
- **Tokens per minute**, which caps the throughput of a single model and therefore sets the wall
  clock for the whole run when models are run in parallel and waited on together.

TPM is the one that surprises people. A model with a generous daily request cap but a small TPM
allowance manages very few trials per minute once the arm count and the completion cap go up, and
it will sit in `Retry-After` sleeps producing `api_error` rows while faster models finish. Measured
on this suite at six conditions and `--max-tokens 2048`: a 12k-TPM model managed about one usable
trial per minute and mostly returned HTTP 429, while 8k-TPM models managed about 2.5 per minute
cleanly. The arithmetic is not intuitive because retries consume the same bucket as the attempts.

So: budget the RUN by the daily request cap, and budget the WALL CLOCK by the slowest model's TPM.
If one model cannot keep up, drop it or give it fewer arms rather than letting it decide when the
comparison finishes. Rows are written and flushed as each trial completes, so a run stopped part
way keeps everything it already measured, and `api_error` rows stay in the file and in the
denominator where they belong.

## Task suite

Before making a release claim, collect at least 30 held-out tasks spanning multi-file
bug fixes, features, refactors, performance work, validation/security guards, Git dirty-tree
handling, and a case where the correct action is to stop for human direction. Include a
never-regress canary suite and keep the final test inputs private until the run is complete.

## Metrics

Report all attempted trials, including infrastructure failures:

| Metric | Definition |
| --- | --- |
| Completion rate | all deterministic acceptance checks pass / all attempted trials |
| Graded check score | mean fraction of each scenario's own checks that passed. Report this alongside completion rate: collapsing a 15-check scenario to one pass/fail bit discards most of the trial's information and multiplies the number of trials needed to detect the same effect |
| **Churn** | lines added plus lines removed, against the starter. **This is the work axis, and it is where this project's central claim actually lives.** "Smallest correct diff" and "deletion over addition" are claims about how much of the file was disturbed, not about tokens spent or checks passed |
| **Work efficiency** | graded checks gained ABOVE THE STARTER, per 10 lines of churn. Two conditions that reach the same score are not equivalent engineering if one changed three lines and the other rewrote the file. Credit only the improvement: measured against the raw score, a submission that changed nothing would rank as maximally efficient |
| Untouched fraction | share of the starter's lines still present verbatim. Low means the file was rewritten to fix one thing |
| pass@1 and pass@3 | one-shot reliability and success within the fixed retry budget |
| Regression rate | previously passing canary checks that fail after the agent run |
| Safety violations | destructive action, secret exposure, or ignored required human pause |
| Cost and latency | provider tokens, wall time, and retries per successful task |
| Process evidence | signal defined, tests actually run, and journal/revert behavior where requested |

Publish raw JSON Lines metadata, prompt hashes, exact tool/model versions, random seed, and
bootstrap confidence intervals, in the same commit as the claim. A number whose rows are not in
the clone is not reproducible. Do not exclude API or grader failures from denominators.

Prefer an interval blocked on (model, scenario) cells. Model strength and scenario difficulty
dominate the variance, so blocking on them tightens the interval substantially without assuming
anything; the residual is the condition effect you are trying to see. State the smallest effect
your trial count could actually have detected, and if that number is larger than the difference
you observed, report the comparison as underpowered rather than ranking the conditions.

## Decision rule

Make `core` the default. Promote `full` only when its lower confidence bound exceeds `core`
by a pre-declared practical margin **and** it does not increase safety violations or
cost-per-success disproportionately. A benchmark win on only the three public starter tasks
is not sufficient evidence.
