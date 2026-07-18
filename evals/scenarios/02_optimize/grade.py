"""Grader for 02_optimize. Kept separate from dedupe.py (the code under test).

Two checks: correctness is the hard gate (the O(n^2) starter already passes it, since it is
correct, just slow), and a scaling ratio that a quadratic implementation fails and a linear
one passes. The ratio is a timing heuristic, so read the printed millisecond numbers too.
"""
import importlib
import os
import sys
import time
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))


def _median_time(fn, repeat=3):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return median(samples)


def checks():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import dedupe
    importlib.reload(dedupe)
    d = dedupe.dedupe

    correct = (
        d([1, 1, 2, 3, 3, 3, 2]) == [1, 2, 3]
        and d([]) == []
        and d(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
        and d([3, 2, 1, 2, 3]) == [3, 2, 1]
    )
    out = [("correctness: order-preserving dedupe", correct, "")]

    # Scaling: time on n and 2n with ~50% duplicates. Linear -> ratio ~2, quadratic -> ~4.
    def make(n):
        half = n // 2 or 1
        return [i % half for i in range(n)]

    n = 2000
    in_n, in_2n = make(n), make(2 * n)
    t1 = _median_time(lambda: d(in_n))
    t2 = _median_time(lambda: d(in_2n))
    ratio = (t2 / t1) if t1 > 0 else float("inf")
    out.append((
        "sub-quadratic scaling: time(2n)/time(n) < 3",
        ratio < 3.0,
        f"ratio={ratio:.1f}, t(n)={t1 * 1000:.1f}ms, t(2n)={t2 * 1000:.1f}ms",
    ))
    return out
