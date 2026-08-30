"""Over-engineered bloated implementation for Scenario 3 (Adversarial test for YAGNI)."""
from __future__ import annotations

import abc
import collections
import threading
import time
from typing import Any, Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class AbstractCacheEntry(abc.ABC, Generic[V]):
    @abc.abstractmethod
    def get_value(self) -> V:
        pass

    @abc.abstractmethod
    def is_expired(self, current_time: float) -> bool:
        pass


class ConcreteCacheEntry(AbstractCacheEntry[V]):
    def __init__(self, value: V, expire_at: float):
        self._value = value
        self._expire_at = expire_at

    def get_value(self) -> V:
        return self._value

    def is_expired(self, current_time: float) -> bool:
        return current_time > self._expire_at


class CacheEntryFactory:
    @staticmethod
    def create_entry(value: Any, ttl: float) -> ConcreteCacheEntry:
        return ConcreteCacheEntry(value, time.monotonic() + ttl)


class AbstractEvictionPolicy(abc.ABC):
    @abc.abstractmethod
    def evict_next(self, storage: dict) -> None:
        pass


class LRUEvictionPolicy(AbstractEvictionPolicy):
    def evict_next(self, storage: collections.OrderedDict) -> None:
        if storage:
            storage.popitem(last=False)


class TTLCache:
    """Over-abstracted cache with 5 classes and 100+ lines."""

    def __init__(self, maxsize: int = 128, ttl_seconds: float = 60.0):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._storage: collections.OrderedDict[Any, ConcreteCacheEntry] = collections.OrderedDict()
        self._eviction_policy = LRUEvictionPolicy()
        self._factory = CacheEntryFactory()
        self._lock = threading.RLock()

    def get(self, key: Any, default: Optional[Any] = None) -> Any:
        with self._lock:
            if key not in self._storage:
                return default
            entry = self._storage[key]
            if entry.is_expired(time.monotonic()):
                del self._storage[key]
                return default
            self._storage.move_to_end(key)
            return entry.get_value()

    def set(self, key: Any, value: Any) -> None:
        with self._lock:
            entry = self._factory.create_entry(value, self._ttl)
            if key in self._storage:
                self._storage.move_to_end(key)
            elif len(self._storage) >= self._maxsize:
                self._eviction_policy.evict_next(self._storage)
            self._storage[key] = entry

    def delete(self, key: Any) -> bool:
        with self._lock:
            return bool(self._storage.pop(key, None) is not None)

    def clear(self) -> None:
        with self._lock:
            self._storage.clear()

    def __len__(self) -> int:
        with self._lock:
            now = time.monotonic()
            expired = [k for k, entry in self._storage.items() if entry.is_expired(now)]
            for k in expired:
                del self._storage[k]
            return len(self._storage)
