# 04_refactor

A report formatting module (`report.py`) that crashes on empty input (`format_report([])` raises `ZeroDivisionError` / `ValueError`) and lacks a modular `calculate_stats(data)` function.

## Task

Fix `format_report` to return `"No data"` when `data` is empty, ensure valid inputs produce the correct report summary, expose a `calculate_stats(data)` function that returns a `(total, average)` tuple (or `(0.0, 0.0)` for empty data), and preserve backward compatibility for `get_summary(data)`.

## Signal

Run `python evals/run.py 04_refactor`.
