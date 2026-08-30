"""Thread-safe token bucket rate limiter."""
from __future__ import annotations

import threading
import time


class RateLimiter:
    """Token bucket rate limiter — thread-safe.

    Args:
        rate: Tokens added per second.
        capacity: Maximum tokens in the bucket.
    """

    def __init__(self, rate: float, capacity: int):
        if rate <= 0 or capacity <= 0:
            raise ValueError("Rate and capacity must be positive.")
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed, False if rejected."""
        if tokens <= 0:
            raise ValueError("Token count must be positive.")
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
