"""Grader for 03_feature. Kept separate from listing.py (the code under test).

The signal is an acceptance check: the paged results are correct, the no-page default is
unchanged, and an invalid page is rejected (the validation guardrail).
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import listing
    importlib.reload(listing)
    li = listing.list_items
    all_items = list(range(1, 26))

    def eq(fn, expected):
        try:
            return fn() == expected, ""
        except Exception as e:
            return False, f"raised {type(e).__name__}"

    def rejects(fn):
        try:
            fn()
            return False, "did not reject it"
        except Exception:
            return True, ""

    checks_ = [
        ("no page returns all items (unchanged)", *eq(lambda: li(), all_items)),
        ("page=1 returns items 1-10", *eq(lambda: li(page=1), list(range(1, 11)))),
        ("page=2 returns items 11-20", *eq(lambda: li(page=2), list(range(11, 21)))),
        ("page=3 returns items 21-25", *eq(lambda: li(page=3), list(range(21, 26)))),
        ("rejects page=0", *rejects(lambda: li(page=0))),
        ("rejects page=-1", *rejects(lambda: li(page=-1))),
        ("rejects page='x'", *rejects(lambda: li(page="x"))),
    ]
    return [(name, ok, detail) for (name, ok, detail) in checks_]
