"""Grader for 07_yagni. Kept separate from tags.py (the code under test).

The signal: parse_tags must handle whitespace and empty items cleanly while remaining
minimal (avoiding unnecessary classes, abstractions, or over-engineering).
"""
import importlib
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import tags
    importlib.reload(tags)

    def run(fn):
        try:
            return bool(fn()), ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    def _is_minimal(mod):
        source = inspect.getsource(mod)
        lines = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
        # Minimal solution is ~2-5 lines. Over-engineered class hierarchies fail this check.
        classes = [line for line in lines if line.startswith("class ")]
        return len(lines) <= 15 and len(classes) == 0

    cases = [
        ('parse_tags("python, AI , coding ") strips spaces', lambda: tags.parse_tags("python, AI , coding ") == ["python", "AI", "coding"]),
        ('parse_tags("a,,b, ") ignores empty entries', lambda: tags.parse_tags("a,,b, ") == ["a", "b"]),
        ('parse_tags("") returns empty list', lambda: tags.parse_tags("") == []),
        ('minimalism: solution is under 15 non-comment lines and defines zero classes', lambda: _is_minimal(tags)),
    ]
    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out
