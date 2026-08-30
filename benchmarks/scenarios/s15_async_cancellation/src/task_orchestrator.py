"""Async worker orchestrator with graceful shutdown and cancellation handling."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine, List, Optional

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Manages concurrent worker coroutines with bounded lifecycle and graceful cancellation."""

    def __init__(self, max_concurrency: int = 4):
        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be positive")
        self.max_concurrency = max_concurrency
        self.queue: asyncio.Queue[Optional[Callable[[], Coroutine[Any, Any, Any]]]] = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self._running = False
        self._results: List[Any] = []

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop processing jobs from the queue until sentinel or cancellation."""
        while self._running:
            try:
                job = await self.queue.get()
                if job is None:
                    self.queue.task_done()
                    break

                try:
                    res = await job()
                    self._results.append(res)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.error("Worker %d job failed: %s", worker_id, exc)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                # Proper cleanup on cancellation
                break

    async def start(self) -> None:
        """Start worker tasks."""
        if self._running:
            return
        self._running = True
        self.workers = [
            asyncio.create_task(self._worker_loop(i), name=f"worker-{i}")
            for i in range(self.max_concurrency)
        ]

    async def submit(self, job: Callable[[], Coroutine[Any, Any, Any]]) -> None:
        """Submit an async job to the queue."""
        if not self._running:
            raise RuntimeError("Orchestrator is not running")
        await self.queue.put(job)

    async def shutdown(self, timeout: float = 2.0) -> List[Any]:
        """Gracefully drain remaining queue items, stop workers, and return results."""
        if not self._running:
            return list(self._results)

        # Wait for submitted jobs to finish processing
        try:
            await asyncio.wait_for(self.queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        self._running = False
        # Push sentinels to unblock any idle workers waiting on get()
        for _ in range(self.max_concurrency):
            await self.queue.put(None)

        try:
            await asyncio.wait_for(asyncio.gather(*self.workers, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            for worker in self.workers:
                if not worker.done():
                    worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()
        return list(self._results)
