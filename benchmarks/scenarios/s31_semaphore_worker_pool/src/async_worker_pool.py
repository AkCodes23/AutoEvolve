"""Bounded async worker pool with semaphore concurrency control."""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, List


async def run_bounded_tasks(
    task_factories: List[Callable[[], Coroutine[Any, Any, Any]]],
    max_concurrency: int = 5,
) -> List[Any]:
    """Execute list of async coroutine factories bounded by a Semaphore."""
    if max_concurrency <= 0:
        raise ValueError("max_concurrency must be positive")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _worker(factory: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
        async with semaphore:
            return await factory()

    tasks = [_worker(tf) for tf in task_factories]
    return await asyncio.gather(*tasks)
