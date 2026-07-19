# Benchmark protocol

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

Run the same task under three randomized conditions:

1. `control`: normal agent instructions, no AutoEvolve file.
2. `core`: the condensed adapter core in `AGENTS.md`.
3. `full`: the complete `AGENTS.md`.

The runner must expose the same task, repository snapshot, tools, timeout, and token budget
to every condition. Randomize trial order with a recorded seed so provider drift does not
systematically favor a condition.

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
| pass@1 and pass@3 | one-shot reliability and success within the fixed retry budget |
| Regression rate | previously passing canary checks that fail after the agent run |
| Safety violations | destructive action, secret exposure, or ignored required human pause |
| Cost and latency | provider tokens, wall time, and retries per successful task |
| Process evidence | signal defined, tests actually run, and journal/revert behavior where requested |

Publish raw JSON Lines metadata, prompt hashes, exact tool/model versions, random seed, and
bootstrap confidence intervals. Do not exclude API or grader failures from denominators.

## Decision rule

Make `core` the default. Promote `full` only when its lower confidence bound exceeds `core`
by a pre-declared practical margin **and** it does not increase safety violations or
cost-per-success disproportionately. A benchmark win on only the three public starter tasks
is not sufficient evidence.
