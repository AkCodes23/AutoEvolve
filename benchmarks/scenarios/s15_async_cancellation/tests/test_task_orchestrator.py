"""Tests for async task lifecycle and graceful cancellation handling."""
import asyncio
import pytest

from benchmarks.scenarios.s15_async_cancellation.src.task_orchestrator import TaskOrchestrator


@pytest.mark.asyncio
async def test_successful_job_execution():
    orchestrator = TaskOrchestrator(max_concurrency=2)
    await orchestrator.start()

    async def sample_job(val: int):
        await asyncio.sleep(0.01)
        return val * 2

    for i in range(5):
        await orchestrator.submit(lambda i=i: sample_job(i))

    results = await orchestrator.shutdown(timeout=1.0)
    assert sorted(results) == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_graceful_cancellation_under_timeout():
    orchestrator = TaskOrchestrator(max_concurrency=2)
    await orchestrator.start()

    async def hanging_job():
        await asyncio.sleep(10.0)
        return "done"

    await orchestrator.submit(hanging_job)

    # Shutdown with short timeout forces task cancellation
    results = await orchestrator.shutdown(timeout=0.05)
    # Ensure all worker tasks are cleaned up
    assert len(orchestrator.workers) == 0
    assert not orchestrator._running


@pytest.mark.asyncio
async def test_submit_to_stopped_orchestrator_raises():
    orchestrator = TaskOrchestrator(max_concurrency=1)
    with pytest.raises(RuntimeError, match="not running"):
        await orchestrator.submit(lambda: asyncio.sleep(0.01))
