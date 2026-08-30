"""Tests for circuit breaker transitions."""
import time
import pytest
from benchmarks.scenarios.s24_circuit_breaker.src.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException


def test_circuit_trips_to_open_after_failures():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def failing_call():
        raise RuntimeError("network down")

    with pytest.raises(RuntimeError):
        cb.call(failing_call)
    with pytest.raises(RuntimeError):
        cb.call(failing_call)

    assert cb.state == "OPEN"

    # Immediate next call fails fast with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        cb.call(lambda: "ok")


def test_circuit_recovers_after_timeout():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    with pytest.raises(RuntimeError):
        cb.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    assert cb.state == "OPEN"
    time.sleep(0.06)

    # Next call executes in HALF-OPEN and resets to CLOSED on success
    res = cb.call(lambda: "recovered")
    assert res == "recovered"
    assert cb.state == "CLOSED"
