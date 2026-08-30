"""Tests for thread-safe leaky bucket rate limiting."""
import threading
import time
from benchmarks.scenarios.s27_leaky_bucket.src.leaky_bucket import LeakyBucket


def test_capacity_burst():
    bucket = LeakyBucket(capacity=3, leak_rate=1.0)
    assert bucket.acquire(1.0) is True
    assert bucket.acquire(1.0) is True
    assert bucket.acquire(1.0) is True
    # 4th burst rejected
    assert bucket.acquire(1.0) is False


def test_leak_recovery():
    bucket = LeakyBucket(capacity=2, leak_rate=20.0)  # 20 units/sec = 1 unit every 50ms
    assert bucket.acquire(2.0) is True
    assert bucket.acquire(1.0) is False

    time.sleep(0.06)  # after 60ms, >1 unit has leaked
    assert bucket.acquire(1.0) is True


def test_multithreaded_acquisition_never_exceeds_capacity():
    bucket = LeakyBucket(capacity=10, leak_rate=1.0)
    success_count = [0]
    lock = threading.Lock()

    def try_acquire():
        if bucket.acquire(1.0):
            with lock:
                success_count[0] += 1

    threads = [threading.Thread(target=try_acquire) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Total accepted burst must not exceed initial capacity (10)
    assert success_count[0] <= 10
