"""Stateful circuit breaker with failure threshold and cooldown."""
from __future__ import annotations

import time
from typing import Any, Callable


class CircuitBreakerOpenException(Exception):
    """Raised when call is attempted on an open circuit."""
    pass


class CircuitBreaker:
    """Stateful circuit breaker (CLOSED -> OPEN -> HALF-OPEN -> CLOSED)."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 0.5):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0

    def call(self, func: Callable[[], Any]) -> Any:
        now = time.monotonic()

        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit is OPEN")

        try:
            result = func()
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise
