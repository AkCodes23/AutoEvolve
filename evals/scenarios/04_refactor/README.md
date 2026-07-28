# 04_refactor

A report formatting module (`report.py`) that crashes on empty input (`format_report([])` raises `ZeroDivisionError` / `ValueError`) and lacks a modular `calculate_stats(data)` function.

## Task

Fix `format_report` to return `"No data"` when `data` is empty, ensure valid inputs produce the same report summary as before, expose a `calculate_stats(data)` function that returns `(total, average)`, have `format_report` actually use that helper instead of repeating the arithmetic, and preserve backward compatibility for `get_summary(data)`.

## Signal

Run `python evals/run.py 04_refactor`.

## What the grader measures

All checks are behavioural: nothing inspects source text, and no check treats an exception as evidence of correctness.

1. `format_report([])` returns `"No data"` rather than raising.
2. Valid input still reports `Total Value: 60.00` and `Average Value: 20.00`.
3. The rest of the report (item count, categories, top value) survives the refactor.
4. A second data set is graded too, so stats cannot be hardcoded to fit the sample.
5. `get_summary` still matches `format_report` and is safe on empty input.
6. `calculate_stats(data)` yields total and average. The container is free: a plain tuple, a `NamedTuple`, a dataclass, or a mapping keyed by `total`/`average` all pass. No exact class or helper signature is required.
7. **Delegation.** The grader replaces the module's `calculate_stats` with a stub returning sentinel numbers and asserts those numbers appear in `format_report`'s output. A `format_report` that recomputes total or average inline (leaving `calculate_stats` as dead duplicated code) fails this check, which is the whole point of the exercise.

Not graded: the value `calculate_stats([])` returns, and the exact wording of anything beyond the lines listed above.
