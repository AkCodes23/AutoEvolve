"""Tests for connection lifecycle and resource cleanup."""
import pytest
from benchmarks.scenarios.s17_resource_lifecycle.src.connection_manager import ConnectionPool


def test_acquire_and_release():
    pool = ConnectionPool(max_size=2)
    with pool.acquire() as conn1:
        assert conn1.is_open
        with pool.acquire() as conn2:
            assert conn2.is_open

    # Both returned to pool; should be able to acquire again
    with pool.acquire() as conn3:
        assert conn3.is_open


def test_pool_exhaustion_timeout():
    pool = ConnectionPool(max_size=1)
    with pool.acquire():
        with pytest.raises(TimeoutError, match="timed out"):
            with pool.acquire(timeout=0.05):
                pass


def test_close_all_cleans_up_resources():
    pool = ConnectionPool(max_size=3)
    pool.close_all()

    # All underlying connections must be closed
    for conn in pool._all_conns:
        assert not conn.is_open

    with pytest.raises(RuntimeError, match="pool is closed"):
        with pool.acquire():
            pass
