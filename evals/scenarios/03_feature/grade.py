"""Grader for 03_feature. Kept separate from listing.py (the code under test).

The signal is an acceptance check on BEHAVIOUR only (no source-text inspection):

1. the no-page default is unchanged (all items, and [] when there are no items),
2. paging is correct for the default per_page AND for a caller-supplied per_page,
   including the ragged final page, so hardcoding 10 cannot score full marks,
3. an invalid page is rejected deliberately: the call must raise ValueError or TypeError
   (either is reasonable for this contract) with a non-empty message. IndexError,
   KeyError and AttributeError count as an incidental crash from unvalidated input,
   which is a FAILURE, and the detail string says so.

KNOWN LIMIT OF THIS RULER, stated so nobody over-reads its numbers. The non-integer rejection
check cannot distinguish deliberate type validation from an incidental TypeError, and no input
can fix that: every non-integer either fails the `page < 1` comparison or fails the slice, and
both raise TypeError. A solution whose only guard is `if page < 1: raise ValueError` therefore
scores full marks. That is defensible, because such a solution does reject every invalid page,
just with a confusing message; but do not read this scenario as evidence that a condition
produced deliberate type validation. The three non-integer cases are deliberately ONE check
rather than three, since three would claim three bits of signal that do not exist.

Two contract decisions, made explicit so neither the solver nor a reader has to guess:

* page=None is the documented "no page" sentinel (it is the starter's default), so it must
  return ALL items. It is not an invalid value.
* page=True is accepted EITHER WAY. bool is an int subclass and True == 1, so the minimal
  correct guard (isinstance(page, int) with no bool special case) treats it as page 1.
  Punishing that would punish the minimal correct answer, so this grader passes both
  "page 1" and "clean rejection", and fails only ignoring the argument or crashing.

The empty-list case is exercised by rebinding the module-level item source to an empty sequence
of the same type, found by shape rather than by name, so a solution that froze the constant into
a tuple or renamed it is not penalized. It runs last and restores the original in a finally
block. The one shape it cannot reach is a list captured once into a default argument.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Deliberate rejection: either is a reasonable choice for this contract.
INTENDED = (ValueError, TypeError)
# Symptoms of no validation at all: the input reached code that was not expecting it.
INCIDENTAL = (IndexError, KeyError, AttributeError)


def _short(value, limit=70):
    text = repr(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _eq(fn, expected):
    """Behavioural equality check with a detail string that shows what came back."""
    try:
        got = fn()
    except Exception as e:  # noqa: BLE001 - any raise here is a failure, and we report it
        return False, f"raised {type(e).__name__}: {_short(str(e))}"
    if got == expected:
        return True, ""
    return False, f"expected {_short(expected)}, got {_short(got)}"


def _rejects(fn):
    """Require a DELIBERATE rejection: ValueError/TypeError with a non-empty message."""
    try:
        got = fn()
    except INCIDENTAL as e:
        return False, (
            f"incidental crash from unvalidated input, not a rejection: "
            f"{type(e).__name__}: {_short(str(e))}"
        )
    except INTENDED as e:
        message = str(e).strip()
        if not message:
            return False, f"raised {type(e).__name__} with an empty message"
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, (
            f"raised {type(e).__name__}: {_short(str(e))}; "
            "expected ValueError or TypeError"
        )
    return False, f"did not reject it, returned {_short(got)}"


def _rejects_all(cases):
    """Every listed value must be rejected. Reports the first that is not."""
    for label, fn in cases:
        ok, detail = _rejects(fn)
        if not ok:
            return False, f"page={label}: {detail}"
    return True, ""


def _page_or_rejects(fn, expected):
    """Accept either outcome (used for page=True): page `expected`, or a clean rejection."""
    try:
        got = fn()
    except INCIDENTAL as e:
        return False, (
            f"incidental crash from unvalidated input: {type(e).__name__}: {_short(str(e))}"
        )
    except INTENDED as e:
        message = str(e).strip()
        if not message:
            return False, f"raised {type(e).__name__} with an empty message"
        return True, f"rejected with {type(e).__name__} (also acceptable)"
    except Exception as e:  # noqa: BLE001
        return False, (
            f"raised {type(e).__name__}: {_short(str(e))}; "
            "expected the first page, ValueError, or TypeError"
        )
    if got == expected:
        return True, "treated as page 1"
    return False, (
        f"neither paged nor rejected: expected {_short(expected)} "
        f"or a ValueError/TypeError, got {_short(got)}"
    )


def _empty_source(listing, li):
    """No page, no items: must return [].

    The item source is found by shape rather than by name, and swapped with setattr rather than
    emptied in place. Requiring a mutable module-level list literally named `_ITEMS` made this
    check fail for a solution that froze the constant into a tuple or renamed it, which is a
    false failure: this project's own coding style asks for immutable data, so freezing that
    constant is the idiomatic choice and must not cost a check.
    """
    candidates = [
        (name, value) for name, value in sorted(vars(listing).items())
        if not name.startswith("__") and isinstance(value, (list, tuple)) and len(value) > 1
    ]
    if not candidates:
        return False, (
            "cannot find a module-level list or tuple holding the items; this grader swaps it "
            "for an empty one to test the no-items case, so keep the item source at module level"
        )
    # The longest sequence is the item source; a shorter one is more likely an unrelated constant.
    name, original = max(candidates, key=lambda pair: len(pair[1]))
    setattr(listing, name, type(original)())
    try:
        return _eq(li, [])
    finally:
        setattr(listing, name, original)


CHECK_NAMES = (
    "no page returns all 25 items unchanged",
    "page=None is the no-page sentinel, returns all items",
    "page=1 returns items 1-10",
    "page=2 returns items 11-20",
    "page=3 returns the ragged final page, items 21-25",
    "page=1, per_page=5 returns exactly items 1-5",
    "page=2, per_page=7 returns items 8-14",
    "page=4, per_page=7 returns the ragged final page, items 22-25",
    "rejects page=0 with ValueError or TypeError",
    "rejects page=-1 with ValueError or TypeError",
    "rejects non-integer page (1.5, '1', 'x'); an incidental TypeError also satisfies this",
    "page=True is page 1 or a clean rejection (bool is an int subclass), either passes",
    "no page with an empty item list returns []",
)


def _checks():
    try:
        import listing
        importlib.reload(listing)
        li = listing.list_items
    except Exception as e:  # noqa: BLE001
        # A submission that will not import is a failing submission, not a harness bug. Return
        # the FULL check set as failed rather than one synthetic check, so checks_total is
        # constant for this scenario: a results table whose denominator changes with the failure
        # mode is hard to read, and pooling it with other rows silently reweights them.
        detail = f"listing.py did not import or expose list_items: {type(e).__name__}: {_short(str(e), 140)}"
        return [(name, False, detail) for name in CHECK_NAMES]
    all_items = list(range(1, 26))  # the scenario ships 25 items: 1..25

    checks_ = [
        # 1. the no-page default must be untouched.
        ("no page returns all 25 items unchanged", *_eq(lambda: li(), all_items)),
        ("page=None is the no-page sentinel, returns all items",
         *_eq(lambda: li(page=None), all_items)),
        # 2. paging with the default per_page, including the ragged final page.
        ("page=1 returns items 1-10", *_eq(lambda: li(page=1), list(range(1, 11)))),
        ("page=2 returns items 11-20", *_eq(lambda: li(page=2), list(range(11, 21)))),
        ("page=3 returns the ragged final page, items 21-25",
         *_eq(lambda: li(page=3), list(range(21, 26)))),
        # 3. per_page must actually be honoured, not hardcoded to 10.
        ("page=1, per_page=5 returns exactly items 1-5",
         *_eq(lambda: li(page=1, per_page=5), list(range(1, 6)))),
        ("page=2, per_page=7 returns items 8-14",
         *_eq(lambda: li(page=2, per_page=7), list(range(8, 15)))),
        ("page=4, per_page=7 returns the ragged final page, items 22-25",
         *_eq(lambda: li(page=4, per_page=7), list(range(22, 26)))),
        # 4. the validation guardrail, one case per kind of invalid input.
        # These two discriminate: an implementation with no validation slices happily for 0 and
        # -1 and silently returns the wrong window, so only a deliberate guard passes them.
        ("rejects page=0 with ValueError or TypeError", *_rejects(lambda: li(page=0))),
        ("rejects page=-1 with ValueError or TypeError", *_rejects(lambda: li(page=-1))),
        # The non-integer cases are ONE check, not three, because they cannot discriminate.
        # Every non-integer either fails the `page < 1` comparison or fails the slice, and both
        # raise TypeError, which is indistinguishable from a deliberate rejection. Scoring them
        # as three separate checks claimed three bits of signal where there are none: a solution
        # with no type validation at all passed all three. There is no value that would fix this
        # (a bool is an int subclass and slices fine, so it is handled separately below as
        # explicitly ambiguous), so the honest move is to stop over-counting.
        ("rejects non-integer page (1.5, '1', 'x'); an incidental TypeError also satisfies this",
         *_rejects_all([("1.5", lambda: li(page=1.5)),
                        ("'1'", lambda: li(page="1")),
                        ("'x'", lambda: li(page="x"))])),
        # bool is an int subclass, so page=True as page 1 or a clean rejection both pass.
        ("page=True is page 1 or a clean rejection (bool is an int subclass), either passes",
         *_page_or_rejects(lambda: li(page=True), list(range(1, 11)))),
        # runs last: it mutates the module-level item list and restores it.
        ("no page with an empty item list returns []", *_empty_source(listing, li)),
    ]
    return [(name, ok, detail) for (name, ok, detail) in checks_]


def checks():
    """Run the graded checks with this scenario's directory on sys.path, then clean up.

    Both the path entry and the imported module are removed afterwards. `run.py --all` grades
    every scenario in ONE interpreter, so a leaked path entry plus a cached module means the
    first scenario to claim a module name wins: a later scenario whose code file shares that
    name would be graded against the wrong file, silently and with a plausible-looking score.
    No two scenarios share a filename today, which is exactly why this is worth fixing now
    rather than after it produces a wrong number.
    """
    added = HERE not in sys.path
    if added:
        sys.path.insert(0, HERE)
    try:
        return _checks()
    finally:
        if added and HERE in sys.path:
            sys.path.remove(HERE)
        for name, module in list(sys.modules.items()):
            origin = getattr(module, "__file__", None) or ""
            if origin and os.path.dirname(os.path.abspath(origin)) == HERE:
                del sys.modules[name]
