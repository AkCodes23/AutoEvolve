"""Grader for 01_bugfix. Kept separate from search.py (the code under test).

The signal: `search("")` and every caller must handle an empty query, and valid queries
must still work. Fixing only one call site leaves the others failing, which is the tell for
a root-cause fix.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import search
    importlib.reload(search)  # pick up the agent's edits on re-run

    def run(fn):
        try:
            return bool(fn()), ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    cases = [
        ('search("") == []', lambda: search.search("") == []),
        ('suggest("") == []', lambda: search.suggest("") == []),
        ('count_matches("") == 0', lambda: search.count_matches("") == 0),
        ('has_match("") is False', lambda: search.has_match("") is False),
        ('search("a") still returns the a-words', lambda: search.search("a") == ["apple", "apricot"]),
    ]
    out = []
    for name, fn in cases:
        ok, detail = run(fn)
        out.append((name, ok, detail))
    return out
