# Benchmark datasets

Raw JSON Lines behind any number published in [`../../docs/RESULTS.md`](../../docs/RESULTS.md).
These are committed on purpose: a claim whose rows are not in the same clone is not reproducible,
and this directory was previously matched by `.gitignore` while the docs cited its contents.

Scores from different grader revisions must not be pooled. Current files carry the revision in
the filename as `g<sha256-prefix>`, computed over every `evals/scenarios/*/grade.py`.

| File | Rows | Status |
| --- | ---: | --- |
| `*.g503e54e3af3b.jsonl` | see file | Current. Grader revision `503e54e3af3b`, the 11-scenario suite, sandboxed. |
| `llama-3.1-8b-instant.g8a4a8f4a1d2c.jsonl` | 70 | Superseded. Grader revision `8a4a8f4a1d2c`, 7-scenario suite, sandboxed, 0 errors. Still valid for what it measured; not poolable with the current revision. |
| `70b_1run.jsonl` | 30 | **VOID.** Do not cite. |
| `70b_xml_benchmark.jsonl` | 35 | **VOID.** Do not cite. |

Predictions for the current run were written before its results were read, in
[`PREREGISTERED.md`](PREREGISTERED.md). Read that first: it names which condition was expected to
lead each scenario and why, so the outcome can be checked against a stated expectation rather than
explained after the fact.

The two void datasets are kept only as the evidence behind the retraction in `docs/RESULTS.md`.
They were produced before the graders were repaired, by rulers since shown to be unable to detect
failure: `02_optimize` passed the untouched O(n^2) starter, `05_security` scored a module
vulnerable in all four advertised ways at 5/5, and `06_errorhandling` gave full marks to a module
whose every function returned `None`. `70b_1run.jsonl` additionally holds 12 `api_error` and 5
`grader_error` rows out of 30, so only 13 of its trials ever produced a verdict. Neither file
records `sandboxed`, and neither is n>1 per cell.

## Re-scoring instead of re-running

Rows written by the current profiler store the graded source, so a grader fix does not require
paying for the same inferences again:

```bash
python3 evals/profile.py --regrade evals/results/<file>.jsonl
```

That writes `<file>.regraded.jsonl` and reports how many scores changed. Verified to reproduce
all 70 current rows exactly when the graders are unchanged. Rename the output with the new
grader revision before publishing it.

## Fields

`model`, `scenario`, `condition`, `trial`, `outcome` (`pass`/`fail`/`api_error`/`grader_error`),
`checks_passed`, `checks_total`, `code` (the graded source), `prompt_tokens`, `prompt_sha256`,
`seed`, `temperature`, `max_tokens`, `sandboxed`, `sandbox_image`, `error`.

Report the graded per-check fraction alongside strict pass. Keep API and grader failures in the
denominator; both appear here with `checks_total` unset, so exclude them from a mean of fractions
but never from the trial count.
