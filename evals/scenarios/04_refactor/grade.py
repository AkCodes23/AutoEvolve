"""Grader for 04_refactor. Kept separate from report.py (the code under test).

Signal: format_report must handle empty input safely without crashing, calculate stats
correctly for valid inputs, and provide helper function calculate_stats.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import report
    importlib.reload(report)

    sample_data = [
        {"category": "Alpha", "value": 10.0},
        {"category": "Beta", "value": 20.0},
        {"category": "Alpha", "value": 30.0},
    ]

    def run(fn):
        try:
            return bool(fn()), ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    cases = [
        ('format_report([]) handles empty list safely', lambda: report.format_report([]) == "No data"),
        ('format_report(sample) total value is 60.00', lambda: "Total Value: 60.00" in report.format_report(sample_data)),
        ('format_report(sample) average value is 20.00', lambda: "Average Value: 20.00" in report.format_report(sample_data)),
        ('get_summary(sample) works via format_report', lambda: report.get_summary(sample_data) == report.format_report(sample_data)),
        ('calculate_stats helper function exists and works', lambda: hasattr(report, "calculate_stats") and report.calculate_stats(sample_data) == (60.0, 20.0)),
    ]
    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out
