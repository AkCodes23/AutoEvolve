"""Grader for 06_errorhandling. Kept separate from pipeline.py (the code under test).

The signal: the agent must add proper input validation, handle edge cases,
categorize errors properly (not swallow them), and preserve valid behavior.
"""
import importlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import pipeline
    importlib.reload(pipeline)

    def run(fn):
        try:
            return bool(fn()), ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    cases = [
        # Input validation
        (
            "process_records(None) raises TypeError or ValueError",
            lambda: _raises_on_none(pipeline),
        ),
        (
            'process_records([{"value": 10}, {"value": 20}]) returns correct result',
            lambda: _valid_records_work(pipeline),
        ),
        (
            "calculate_average([]) raises ValueError (not ZeroDivisionError)",
            lambda: _avg_empty_raises_valueerror(pipeline),
        ),
        (
            "calculate_average([1, 2, 3]) returns 2.0",
            lambda: pipeline.calculate_average([1, 2, 3]) == 2.0,
        ),
        (
            'parse_date("not-a-date") raises ValueError',
            lambda: _parse_rejects_garbage(pipeline),
        ),
        (
            'parse_date("2024-03-15") returns correct dict',
            lambda: pipeline.parse_date("2024-03-15") == {"year": 2024, "month": 3, "day": 15},
        ),
        (
            "write_output returns False on write failure (not silent True)",
            lambda: _write_reports_failure(pipeline),
        ),
    ]
    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out


def _raises_on_none(mod):
    try:
        mod.process_records(None)
        return False  # Should have raised
    except (TypeError, ValueError):
        return True
    except Exception:
        return False  # Wrong exception type


def _valid_records_work(mod):
    result = mod.process_records([{"value": 10}, {"value": 20}])
    return (
        isinstance(result, dict)
        and result.get("total") == 30
        and result.get("count") == 2
        and result.get("average") == 15.0
    )


def _avg_empty_raises_valueerror(mod):
    try:
        mod.calculate_average([])
        return False
    except ValueError:
        return True
    except ZeroDivisionError:
        return False  # Should be ValueError, not raw ZeroDivisionError


def _parse_rejects_garbage(mod):
    try:
        mod.parse_date("not-a-date")
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _write_reports_failure(mod):
    """write_output must return False (or raise) when writing to an invalid path."""
    result = mod.write_output({"key": "value"}, "/nonexistent/dir/file.txt")
    return result is False or result is None
