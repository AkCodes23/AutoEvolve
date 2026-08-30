# Scenario 4: Context Frugality & Log Management

## Task Description
An end-to-end data transformation pipeline test suite `tests/test_pipeline_noisy.py` emits over 12,000 lines of debug and socket trace logs while verifying stream processing. One test in the suite, `test_scale_normalization`, fails due to a scale calculation bug in `src/pipeline/transformer.py`.

The task is to diagnose and fix the scaling bug in `normalize_scale` in `src/pipeline/transformer.py` so that normalized outputs achieve the exact target standard deviation without introducing context flooding.

## Constraints
- Modify ONLY `src/pipeline/transformer.py`.
 - Do NOT flood the agent context with 12,000 lines of stdout. Use quiet execution (`pytest -q --tb=short`, or redirect full output to a log file and read only the summary tail) to inspect failure tails without ingesting multi-megabyte log dumps.
