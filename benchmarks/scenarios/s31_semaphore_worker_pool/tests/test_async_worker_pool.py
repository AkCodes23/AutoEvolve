"""Tests for bounded async semaphore worker pool."""
import asyncio
import pytest
from benchmarks.scenarios.s31_semaphore_worker_pool.src.async_worker_pool import run_bounded_tasks


@pytest.mark.asyncio
async def test_bounded_concurrency_never_exceeds_max():
    active_count = 0
    max_observed_active = 0
    lock = asyncio.Lock()

    async def mock_network_fetch(val: int):
        nonlocal active_count, max_observed_active
        async with lock:
            active_count += 1
            if active_count > max_observed_active:
                max_observed_active = active_count

        await asyncio.sleep(0.02)

        async with lock:
            active_count -= 1
        return val * 10

    factories = [lambda i=i: mock_network_fetch(i) for i in range(20)]
    results = await run_bounded_tasks(factories, max_concurrency=4)

    assert len(results) == 20
    assert results[0] == 0
    assert results[19] == 190
    # Peak active workers must never exceed 4
    assert max_observed_active <= 4
