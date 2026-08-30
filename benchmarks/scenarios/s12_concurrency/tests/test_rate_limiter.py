"""Tests for thread-safe rate limiter — includes concurrent stress tests."""
from __future__ import annotations

import ast
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from benchmarks.scenarios.s12_concurrency.src.rate_limiter import RateLimiter


class TestBasicBehavior:
    def test_initial_capacity(self):
        rl = RateLimiter(rate=10.0, capacity=5)
        assert rl.acquire(5) is True
        assert rl.acquire(1) is False

    def test_refill_over_time(self):
        rl = RateLimiter(rate=100.0, capacity=10)
        rl.acquire(10)
        time.sleep(0.15)
        assert rl.acquire(1) is True

    def test_reject_when_empty(self):
        rl = RateLimiter(rate=1.0, capacity=1)
        rl.acquire(1)
        assert rl.acquire(1) is False

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            RateLimiter(rate=-1, capacity=10)
        with pytest.raises(ValueError):
            RateLimiter(rate=10, capacity=0)

    def test_acquire_zero_raises(self):
        rl = RateLimiter(rate=10.0, capacity=5)
        with pytest.raises(ValueError):
            rl.acquire(0)


class TestConcurrentSafety:
    def test_no_overdraft_under_contention(self):
        capacity = 100
        rl = RateLimiter(rate=0.0001, capacity=capacity)
        successes = []

        def try_acquire():
            if rl.acquire(1):
                successes.append(1)

        threads = [threading.Thread(target=try_acquire) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = len(successes)
        assert total <= capacity, (
            f"Overdraft detected: {total} acquires succeeded with capacity {capacity}"
        )

    def test_concurrent_executor_no_overdraft(self):
        capacity = 50
        rl = RateLimiter(rate=0.0001, capacity=capacity)
        results = []

        def worker():
            return rl.acquire(1)

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(worker) for _ in range(200)]
            results = [f.result() for f in futures]

        successes = sum(1 for r in results if r)
        assert successes <= capacity, (
            f"Overdraft: {successes} > {capacity}"
        )


class TestSourceCodeThreadSafety:
    """AST-level verification that locking is present."""

    def test_has_threading_lock(self):
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "rate_limiter.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "threading" in source, "Expected threading module usage"
        assert "Lock" in source or "lock" in source, "Expected Lock usage for thread safety"

    def test_uses_monotonic_clock(self):
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "rate_limiter.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "monotonic" in source, (
            "Expected time.monotonic() for reliable elapsed time measurement"
        )
