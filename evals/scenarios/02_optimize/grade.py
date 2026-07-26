"""Grader for 02_optimize. Kept separate from dedupe.py (the code under test).

Two checks: correctness is the hard gate (the O(n^2) starter already passes it, since it is
correct, just slow), and a sub-quadratic scaling check measured via step tracing and timing.
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


def _count_steps(fn):
    steps = 0

    def tracer(frame, event, arg):
        nonlocal steps
        if event == "line":
            steps += 1
        return tracer

    sys.settrace(tracer)
    try:
        fn()
    finally:
        sys.settrace(None)
    return steps


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

    def make(n):
        half = n // 2 or 1
        return [i % half for i in range(n)]

    n = 2000
    in_n, in_2n = make(n), make(2 * n)
    t1 = _median_time(lambda: d(in_n))
    t2 = _median_time(lambda: d(in_2n))
    ratio = (t2 / t1) if t1 > 0 else float("inf")

    steps_2n = _count_steps(lambda: d(in_2n))
    # Linear algorithm takes ~4,000-12,000 line steps for N=4000; quadratic takes >50,000.
    is_linear = (steps_2n < 20000) or (ratio < 3.0)

    out.append((
        "sub-quadratic scaling: O(n) complexity check",
        is_linear,
        f"steps(2n)={steps_2n}, ratio={ratio:.1f}, t(n)={t1 * 1000:.1f}ms, t(2n)={t2 * 1000:.1f}ms",
    ))
    return out
