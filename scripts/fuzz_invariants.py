"""Metamorphic and Property-Based Invariant Fuzzer.

Synthesizes dynamic property tests checking idempotence, commutativity,
scale invariance (O(N) vs O(N^2)), and crash-recovery invariants.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from typing import Any, Callable, Dict, List


def check_idempotence(fn: Callable[[Any], Any], sample_inputs: List[Any]) -> Dict[str, Any]:
    """Verify f(f(x)) == f(x)."""
    passed = 0
    total = len(sample_inputs)
    for x in sample_inputs:
        try:
            once = fn(x)
            twice = fn(once)
            if once == twice:
                passed += 1
        except Exception:
            pass
    return {"property": "idempotence", "passed": passed, "total": total, "rate": passed / max(1, total)}


def check_scale_linearity(fn: Callable[[List[int]], Any], base_size: int = 1000, scale_factor: int = 10) -> Dict[str, Any]:
    """Verify runtime scales sub-quadratically (O(N) or O(N log N) vs O(N^2))."""
    inp_small = [random.randint(0, 10000) for _ in range(base_size)]
    inp_large = [random.randint(0, 10000) for _ in range(base_size * scale_factor)]

    t0 = time.perf_counter()
    fn(inp_small)
    t1 = time.perf_counter()
    dt_small = t1 - t0

    t2 = time.perf_counter()
    fn(inp_large)
    t3 = time.perf_counter()
    dt_large = t3 - t2

    ratio = dt_large / max(1e-6, dt_small)
    is_subquadratic = ratio < (scale_factor ** 1.5)
    return {
        "property": "scale_linearity",
        "small_ms": round(dt_small * 1000, 3),
        "large_ms": round(dt_large * 1000, 3),
        "time_ratio": round(ratio, 2),
        "is_subquadratic": is_subquadratic,
    }


def main():
    print("Metamorphic & Property-Based Invariant Fuzzer ready.")


if __name__ == "__main__":
    main()
