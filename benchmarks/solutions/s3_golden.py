"""Golden minimal implementation for Scenario 3: TTLCache."""
from __future__ import annotations

import collections
import threading
import time


class TTLCache:
    """Thread-safe LRU Cache with TTL expiration in ~30 lines."""

    def __init__(self, maxsize: int = 128, ttl_seconds: float = 60.0):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self._cache: collections.OrderedDict = collections.OrderedDict()
        self._lock = threading.RLock()

    def get(self, key, default=None):
        with self._lock:
            if key not in self._cache:
                return default
            val, expire_at = self._cache[key]
            if time.monotonic() > expire_at:
                del self._cache[key]
                return default
            self._cache.move_to_end(key)
            return val

    def set(self, key, value) -> None:
        with self._lock:
            expire_at = time.monotonic() + self.ttl
            if key in self._cache:
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = (value, expire_at)

    def delete(self, key) -> bool:
        with self._lock:
            return bool(self._cache.pop(key, None) is not None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            now = time.monotonic()
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]
            return len(self._cache)
