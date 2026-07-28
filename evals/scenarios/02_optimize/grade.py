"""Grader for 02_optimize. Kept separate from dedupe.py (the code under test).

Three checks: correctness is the hard gate (the O(n^2) starter already passes it, since it is
correct, just slow), the caller's list must not be modified in place, and a sub-quadratic
scaling gate. The middle one exists so the scenario is not effectively binary: the scaling gate
cannot pass while correctness fails, so without an independent third probe only two scores were
reachable and a trial here carried close to one bit.

The scaling gate counts the work a dedupe can actually use to tell elements apart: calls to
__eq__ and __hash__. Two earlier designs were both bypassable and are recorded here so they do
not come back:

  1. sys.settrace LINE events. The comparing inside `x not in out` happens in C, so the O(n^2)
     starter registered about n line events for n^2 comparisons and passed.
  2. Wall-clock scaling as a gate. Measured over 100 trials it false-fails correct code 1 to 2
     percent of runs and false-passes the quadratic starter about 8 percent, and the
     distributions overlap, so no threshold separates them. Timing is reported below as an
     advisory number and is deliberately NOT part of the verdict: a grader whose result depends
     on machine load is not a frozen signal.

The probe element exposes no readable payload. An earlier probe stored its value in a `value`
attribute, which let a quadratic solution compare `x.value` directly and score zero
comparisons. Values live in a side table keyed by id() instead.
"""
import importlib
import os
import sys
import time
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))

# A correct hash-based pass costs a small constant per element: one hash on insert plus a
# comparison on a hash hit. A list scan costs about n/4 comparisons per element. Measured:
# dict.fromkeys and set both land near 1.5 per element, the quadratic starter near 1000.
PROBES_PER_ELEMENT_BUDGET = 20


def _probe(dedupe_fn, values):
    """Run dedupe over opaque elements, counting every == and hash() it performs.

    Returns (probe_count, status) where status is 'ok', 'wrong', or 'raised <ExceptionName>'.
    """
    probes = 0
    payload = {}

    class Element:
        # No attributes: a solution cannot read the value it is deduplicating, so the only way
        # to distinguish two elements is to compare or hash them, which is what we count.
        __slots__ = ()

        def __eq__(self, other):
            nonlocal probes
            probes += 1
            return type(other) is Element and payload[id(self)] == payload[id(other)]

        def __hash__(self):
            nonlocal probes
            probes += 1
            return hash(payload[id(self)])

    items = []
    first = {}
    for value in values:
        element = Element()
        payload[id(element)] = value
        items.append(element)
        first.setdefault(value, element)

    try:
        result = dedupe_fn(list(items))
    except Exception as exc:  # noqa: BLE001 - a dedupe that only works on ints is not general
        return probes, f"raised {type(exc).__name__}"

    count = probes
    expected = list(first.values())
    ok = (
        isinstance(result, list)
        and len(result) == len(expected)
        # Identity, not equality: comparing here would add probes and, worse, a solution that
        # returned fresh equal objects would look correct while having lost the originals.
        and all(a is b for a, b in zip(result, expected))
    )
    return count, ("ok" if ok else "wrong")


def _median_time(fn, repeat=5):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return median(samples)


CHECK_NAMES = (
    "correctness: order-preserving dedupe",
    "the caller's list is not modified in place",
    f"sub-quadratic scaling: at most {PROBES_PER_ELEMENT_BUDGET} comparisons per element",
)


def _safe(fn, default):
    """Run fn, absorbing a candidate's exception into a detail string.

    A broken answer must be scored, not allowed to abort checks(). If an exception escaped,
    run.py would print "[ERROR] the grader itself failed to run (this is a harness bug)" and
    evals/profile.py would record outcome=grader_error with checks_total=None, which DROPS
    the trial from the published averages instead of scoring it zero.
    """
    try:
        return fn(), ""
    except Exception as exc:  # noqa: BLE001 - a failing candidate is a failed check
        return default, f"raised {type(exc).__name__}: {exc}"


def checks():
    added_path = HERE not in sys.path
    if added_path:
        sys.path.insert(0, HERE)
    try:
        try:
            import dedupe
            importlib.reload(dedupe)
            d = dedupe.dedupe
            if not callable(d):
                raise TypeError(f"dedupe is {type(d).__name__}, not callable")
        except Exception as exc:  # noqa: BLE001 - see _safe: this must not look like a bug
            detail = f"dedupe.py did not provide a usable dedupe(): {type(exc).__name__}: {exc}"
            return [(name, False, detail) for name in CHECK_NAMES]

        correct, why = _safe(lambda: (
            d([1, 1, 2, 3, 3, 3, 2]) == [1, 2, 3]
            and d([]) == []
            and d(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
            and d([3, 2, 1, 2, 3]) == [3, 2, 1]
            # A hash collision. In CPython hash(-1) == hash(-2) == -2, so a solution that
            # deduplicates on the hash alone and never on equality collapses these two distinct
            # values into one. Without this input such a solution passed both checks: it is
            # correct on collision-free data and spends one hash per element, which is under the
            # comparison budget. Deduplicating requires equality, not just hashing.
            and d([-1, -2, -1]) == [-1, -2]
        ), False)
        out = [(CHECK_NAMES[0], bool(correct), why)]

        # An independent probe: this one can fail on its own, for its own reason. With only a
        # correctness check and a scaling check (which cannot pass while correctness fails), the
        # scenario had just two reachable scores and carried close to one bit. dedupe returns a
        # new list, so an in-place rewrite of the caller's data is a real contract break and a
        # classic optimisation shortcut.
        def _no_mutation():
            original = [3, 1, 3, 2, 1]
            supplied = list(original)
            d(supplied)
            if supplied != original:
                return False, f"the input list was modified in place: {supplied!r} (was {original!r})"
            return True, ""

        try:
            mutated_ok, mutated_why = _no_mutation()
        except Exception as exc:  # noqa: BLE001 - a candidate that raises here has failed
            mutated_ok, mutated_why = False, f"raised {type(exc).__name__}: {exc}"
        out.append((CHECK_NAMES[1], bool(mutated_ok), mutated_why))

        n = 2000
        values = [i % n for i in range(2 * n)]
        probes, status = _probe(d, values)
        budget = PROBES_PER_ELEMENT_BUDGET * len(values)
        is_linear = status == "ok" and probes <= budget

        # Advisory only. Reported so a human can sanity-check the verdict, never gated on.
        t1, _ = _safe(lambda: _median_time(lambda: d([i % (n // 2) for i in range(n)])), 0.0)
        t2, _ = _safe(lambda: _median_time(lambda: d(list(values))), 0.0)
        ratio = (t2 / t1) if t1 > 0 else float("inf")

        out.append((
            CHECK_NAMES[2],
            bool(is_linear),
            f"probes(2n)={probes} (budget {budget}), result={status}; "
            f"advisory timing ratio={ratio:.1f} (t(n)={t1 * 1000:.1f}ms, t(2n)={t2 * 1000:.1f}ms)",
        ))
        return out
    finally:
        if added_path and HERE in sys.path:
            sys.path.remove(HERE)
        # Drop the cached submission module too. `run.py --all` grades every scenario in one
        # interpreter, and a module left in sys.modules would shadow a later scenario that
        # happens to use the same filename, grading the wrong file with a plausible score.
        for name, module in list(sys.modules.items()):
            origin = getattr(module, "__file__", None) or ""
            if origin and os.path.dirname(os.path.abspath(origin)) == HERE:
                del sys.modules[name]
