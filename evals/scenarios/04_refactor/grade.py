"""Grader for 04_refactor. Kept separate from report.py (the code under test).

Signal, all measured by BEHAVIOUR (never by reading source text):
  1. format_report([]) returns "No data" instead of crashing.
  2. format_report(sample) still reports the same stats it always did.
  3. get_summary stays a working front door for both shapes of input.
  4. calculate_stats(data) yields (total, average), graded on two different data
     sets so the numbers cannot be hardcoded to fit the grader's sample.
  5. format_report actually DELEGATES to calculate_stats. This is the point of the
     exercise, so it is probed by patching the module's calculate_stats with a
     sentinel and asserting the sentinel reaches format_report's output. A
     format_report that re-derives the arithmetic inline (leaving calculate_stats
     as dead, duplicated code) cannot pass this check.

The sentinel duck-types every legitimate return shape (plain tuple, NamedTuple,
dataclass, mapping), so a solution is never punished for its choice of container.
"""
import importlib
import math
import os
import sys
from collections.abc import Mapping, Sequence
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))

# Distinctive sentinel stats. The average is deliberately NOT total / 3, so an
# implementation that takes the total from the helper and recomputes the average
# itself (still duplicating half the extracted arithmetic) is detected too. Both
# stay under 1000 so a thousands-separator format spec cannot hide them.
SENTINEL_TOTAL = 811.25
SENTINEL_AVERAGE = 46.5
SENTINEL_TOTAL_TEXT = "811.25"
SENTINEL_AVERAGE_TEXT = "46.5"  # also matches a "46.50" two-decimal rendering

_TOTAL_KEYS = ("total", "sum")
_AVERAGE_KEYS = ("average", "avg", "mean")

# Single source for the check names, so an unimportable submission can still be reported as
# a full set of failed checks. If the import escaped checks(), run.py would print "[ERROR]
# the grader itself failed to run (this is a harness bug)" and evals/profile.py would record
# outcome=grader_error with checks_total=None, dropping the trial from the published averages
# instead of scoring it zero.
CHECK_NAMES = (
    "format_report([]) returns 'No data' instead of crashing",
    "format_report(sample) reports Total Value: 60.00",
    "format_report(sample) reports Average Value: 20.00",
    "format_report(sample) preserves count, categories and top value",
    "format_report(other) recomputes stats for a different data set",
    "get_summary still works for sample and empty input",
    "calculate_stats yields (60.0, 20.0) for sample and (7.5, 3.75) for other",
    "format_report delegates to calculate_stats (stubbed helper reaches output)",
)


class _StatsProbe(tuple):
    """Stand-in return value for calculate_stats that supports every sane access style.

    Tuple unpacking and integer indexing come from tuple itself; string keys,
    attributes, and a small mapping surface are added so that format_report can
    read the sentinel however its author chose to consume the helper.
    """

    __slots__ = ()
    _fields = ("total", "average")

    def __new__(cls):
        return super().__new__(cls, (SENTINEL_TOTAL, SENTINEL_AVERAGE))

    @property
    def total(self):
        return tuple.__getitem__(self, 0)

    @property
    def average(self):
        return tuple.__getitem__(self, 1)

    @property
    def avg(self):
        return tuple.__getitem__(self, 1)

    @property
    def mean(self):
        return tuple.__getitem__(self, 1)

    def __getitem__(self, key):
        if isinstance(key, str):
            if key in _TOTAL_KEYS:
                return SENTINEL_TOTAL
            if key in _AVERAGE_KEYS:
                return SENTINEL_AVERAGE
            raise KeyError(key)
        return tuple.__getitem__(self, key)

    def keys(self):
        return ("total", "average")

    def values(self):
        return (SENTINEL_TOTAL, SENTINEL_AVERAGE)

    def items(self):
        return tuple(zip(self.keys(), self.values()))

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError, TypeError):
            return default

    def _asdict(self):
        return {"total": SENTINEL_TOTAL, "average": SENTINEL_AVERAGE}


def _first(container, names, getter):
    for name in names:
        try:
            return True, getter(container, name)
        except Exception:
            continue
    return False, None


def _extract_stats(result):
    """Pull (total, average) out of any legitimate return shape, else None.

    Accepted: a 2-item sequence (plain tuple, list, NamedTuple), an object
    exposing total/average attributes (NamedTuple, dataclass, custom class), or
    a mapping keyed by total/average. No exact class is required.
    """
    if isinstance(result, Mapping):
        ok_t, total = _first(result, _TOTAL_KEYS, lambda c, k: c[k])
        ok_a, average = _first(result, _AVERAGE_KEYS, lambda c, k: c[k])
        return (total, average) if ok_t and ok_a else None

    ok_t, total = _first(result, _TOTAL_KEYS, getattr)
    ok_a, average = _first(result, _AVERAGE_KEYS, getattr)
    if ok_t and ok_a:
        return (total, average)

    if isinstance(result, Sequence) and not isinstance(result, (str, bytes)) and len(result) == 2:
        return (result[0], result[1])
    return None


def _close(value, expected):
    """Numeric comparison that accepts int, float, Decimal, Fraction and friends."""
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isclose(number, expected, rel_tol=0.0, abs_tol=1e-9)


def _text(value):
    return value if isinstance(value, str) else ""


def _checks():
    try:
        import report
        importlib.reload(report)
    except Exception as e:  # noqa: BLE001 - an unusable submission fails, it is not a bug
        reason = f"report.py did not import: {type(e).__name__}: {e}"[:160]
        return [(name, False, reason) for name in CHECK_NAMES]

    sample_data = [
        {"category": "Alpha", "value": 10.0},
        {"category": "Beta", "value": 20.0},
        {"category": "Alpha", "value": 30.0},
    ]
    # A second data set, so stats have to be computed rather than hardcoded.
    other_data = [
        {"category": "Gamma", "value": 5.0},
        {"category": "Delta", "value": 2.5},
    ]

    def empty_is_safe():
        out = report.format_report([])
        return isinstance(out, str) and out.strip() == "No data"

    def preserves_details():
        out = _text(report.format_report(sample_data))
        missing = [
            part for part in ("Total Items: 3", "Alpha", "Beta", "30.00")
            if part not in out
        ]
        return (not missing), ("missing " + ", ".join(missing) if missing else "")

    def summary_preserved():
        same = report.get_summary(sample_data) == report.format_report(sample_data)
        empty = report.get_summary([])
        safe_empty = isinstance(empty, str) and empty.strip() == "No data"
        if not same:
            return False, "get_summary(sample) diverged from format_report"
        if not safe_empty:
            return False, "get_summary([]) did not return 'No data'"
        return True, ""

    def stats_helper():
        for data, want_total, want_average in (
            (sample_data, 60.0, 20.0),
            (other_data, 7.5, 3.75),
        ):
            stats = _extract_stats(report.calculate_stats(data))
            if stats is None:
                return False, "return value exposes neither (total, average) nor total/average"
            total, average = stats
            if not _close(total, want_total):
                return False, f"total was {total!r}, expected {want_total}"
            if not _close(average, want_average):
                return False, f"average was {average!r}, expected {want_average}"
        return True, ""

    def recomputes_per_input():
        out = _text(report.format_report(other_data))
        missing = [
            part for part in ("Total Items: 2", "Total Value: 7.50", "Average Value: 3.75",
                              "Delta", "Gamma")
            if part not in out
        ]
        return (not missing), ("missing " + ", ".join(missing) if missing else "")

    def _saw_sentinel(out):
        return SENTINEL_TOTAL_TEXT in out, SENTINEL_AVERAGE_TEXT in out

    def _delegates_via_code_swap():
        """Second attempt: replace the helper's __code__ rather than the module attribute.

        `patch.object` only intercepts a call that looks the attribute up on the module at call
        time. A solution that captured the FUNCTION OBJECT instead, by aliasing it at module
        level (`_stats = calculate_stats`) or binding it as a default argument, genuinely does
        delegate but is invisible to attribute patching. Swapping the code object reaches those
        forms, because every alias points at the same function.

        Returns None when the swap is not possible, so the caller can say "cannot determine"
        rather than silently reporting a legitimate solution as a reimplementation.
        """
        helper = getattr(report, "calculate_stats", None)
        original = getattr(helper, "__code__", None)
        if original is None:
            return None

        # A swapped code object runs against the SUBMISSION module's globals, not this
        # grader's, so the stub cannot close over anything here. Compile it separately so its
        # only global reference is a name we inject into that module, then remove both.
        factory = "_autoevolve_probe_factory"
        namespace = {}
        exec(compile(f"def _stub(*args, **kwargs):\n    return {factory}()\n",
                     "<autoevolve-delegation-probe>", "exec"), namespace)
        setattr(report, factory, _StatsProbe)
        try:
            helper.__code__ = namespace["_stub"].__code__
        except (AttributeError, TypeError, ValueError):
            delattr(report, factory)
            return None
        try:
            return _saw_sentinel(_text(report.format_report(sample_data)))
        except Exception:  # noqa: BLE001 - a crash under the stub is not evidence either way
            return None
        finally:
            helper.__code__ = original
            if hasattr(report, factory):
                delattr(report, factory)

    def delegates_to_helper():
        # Patch the module attribute that format_report resolves at call time. No
        # reload happens inside the patch, so the real helper is restored cleanly.
        probe = _StatsProbe()
        with patch.object(report, "calculate_stats", lambda *a, **k: probe):
            out = _text(report.format_report(sample_data))
        seen_total, seen_average = _saw_sentinel(out)
        if seen_total and seen_average:
            return True, ""
        if seen_total or seen_average:
            which = "average" if seen_total else "total"
            return False, f"format_report recomputes the {which} instead of using the helper"

        # Nothing got through. Before calling this a reimplementation, rule out the aliasing
        # forms, which used to produce a verdict identical to the genuine cheat's.
        swapped = _delegates_via_code_swap()
        if swapped is None:
            return False, ("stubbed calculate_stats had no effect on the output, and the helper "
                           "could not be probed further, so delegation could not be confirmed")
        if all(swapped):
            return True, ("delegates through an alias or a captured default argument rather "
                          "than a module-level lookup, which still counts as reuse")
        return False, ("format_report does not call calculate_stats at all: neither stubbing the "
                       "module attribute nor replacing the helper's code changed the output, so "
                       "the statistics are recomputed inline")

    # Order matches CHECK_NAMES, which is the single source for the names.
    probes = (
        empty_is_safe,
        lambda: "Total Value: 60.00" in _text(report.format_report(sample_data)),
        lambda: "Average Value: 20.00" in _text(report.format_report(sample_data)),
        preserves_details,
        recomputes_per_input,
        summary_preserved,
        stats_helper,
        delegates_to_helper,
    )
    cases = list(zip(CHECK_NAMES, probes))

    out = []
    for name, fn in cases:
        try:
            res = fn()
        except Exception as e:
            ok, detail = False, f"raised {type(e).__name__}: {e}"[:120]
        else:
            if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], bool):
                ok, detail = res
            else:
                ok, detail = bool(res), ""
        out.append((name, ok, detail))
    return out


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
