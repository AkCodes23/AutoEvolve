"""Thread-safe leaky bucket rate limiter using monotonic clock."""
from __future__ import annotations

import threading
import time


class LeakyBucket:
    """Thread-safe rate limiter with steady leak rate."""

    def __init__(self, capacity: int, leak_rate: float):
        if capacity <= 0 or leak_rate <= 0:
            raise ValueError("Capacity and leak_rate must be positive")
        self.capacity = capacity
        self.leak_rate = leak_rate  # units per second
        self.water = 0.0
        self.last_leak_time = time.monotonic()
        self._lock = threading.Lock()

    def _leak(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_leak_time
        leaked = elapsed * self.leak_rate
        self.water = max(0.0, self.water - leaked)
        self.last_leak_time = now

    def acquire(self, amount: float = 1.0) -> bool:
        """Attempt to add amount to bucket. Returns True if accepted, False if overflow."""
        with self._lock:
            self._leak()
            if self.water + amount <= self.capacity:
                self.water += amount
                return True
            return False
