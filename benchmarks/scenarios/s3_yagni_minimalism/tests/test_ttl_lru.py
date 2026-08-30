import threading
import time
import pytest
from benchmarks.scenarios.s3_yagni_minimalism.src.cache.ttl_lru import TTLCache


def test_basic_set_and_get():
    cache = TTLCache(maxsize=10, ttl_seconds=60.0)
    cache.set("k1", "v1")
    assert cache.get("k1") == "v1"
    assert cache.get("k_missing") is None
    assert cache.get("k_missing", "default_val") == "default_val"


def test_lru_eviction_on_capacity():
    # Cache capacity of 3
    cache = TTLCache(maxsize=3, ttl_seconds=60.0)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    # Access 'a' to make it most recently used; 'b' is now LRU
    assert cache.get("a") == 1

    # Adding 'd' should evict 'b'
    cache.set("d", 4)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_ttl_expiration(monkeypatch):
    current_time = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: current_time[0])

    cache = TTLCache(maxsize=5, ttl_seconds=10.0)
    cache.set("k1", "v1")
    assert cache.get("k1") == "v1"

    # Advance time within TTL
    current_time[0] += 5.0
    assert cache.get("k1") == "v1"

    # Advance time beyond TTL (1000 + 10.1 > 1010)
    current_time[0] += 5.1
    assert cache.get("k1") is None
    assert len(cache) == 0


def test_delete_operation():
    cache = TTLCache(maxsize=5, ttl_seconds=60.0)
    cache.set("key1", "val1")
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert cache.delete("key1") is False


def test_clear_operation():
    cache = TTLCache(maxsize=5, ttl_seconds=60.0)
    cache.set("k1", 1)
    cache.set("k2", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
    assert cache.get("k1") is None


def test_len_prunes_expired(monkeypatch):
    current_time = [100.0]
    monkeypatch.setattr(time, "monotonic", lambda: current_time[0])

    cache = TTLCache(maxsize=5, ttl_seconds=5.0)
    cache.set("a", 1)
    current_time[0] += 3.0
    cache.set("b", 2)

    assert len(cache) == 2

    # Advance to 106.0: 'a' expired (set at 100, exp 105), 'b' valid (set at 103, exp 108)
    current_time[0] += 3.0
    assert len(cache) == 1
    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_invalid_constructor_arguments():
    with pytest.raises(ValueError):
        TTLCache(maxsize=0)
    with pytest.raises(ValueError):
        TTLCache(maxsize=-5)
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=0)
    with pytest.raises(ValueError):
        TTLCache(ttl_seconds=-10.0)


def test_multithreaded_concurrency():
    cache = TTLCache(maxsize=50, ttl_seconds=10.0)
    num_threads = 10
    ops_per_thread = 200

    def worker(tid: int):
        for i in range(ops_per_thread):
            key = f"k_{i % 20}"
            cache.set(key, f"val_{tid}_{i}")
            _ = cache.get(key)
            if i % 10 == 0:
                cache.delete(key)
            if i % 25 == 0:
                _ = len(cache)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Cache should be in consistent state without deadlocks or crashes
    assert len(cache) <= 50
