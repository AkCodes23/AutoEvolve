"""Connection pool with bounded lifecycle, timeout management, and context managers."""
from __future__ import annotations

import contextlib
import queue
import time
from typing import Generator, List, Optional


class ManagedConnection:
    def __init__(self, conn_id: int):
        self.conn_id = conn_id
        self.is_open = True

    def close(self) -> None:
        self.is_open = False


class ConnectionPool:
    """Bounded connection pool with context manager acquisition and leak-free teardown."""

    def __init__(self, max_size: int = 5):
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self.max_size = max_size
        self._pool: queue.Queue[ManagedConnection] = queue.Queue(maxsize=max_size)
        self._all_conns: List[ManagedConnection] = []
        self._closed = False

        for i in range(max_size):
            conn = ManagedConnection(conn_id=i)
            self._all_conns.append(conn)
            self._pool.put(conn)

    @contextlib.contextmanager
    def acquire(self, timeout: float = 1.0) -> Generator[ManagedConnection, None, None]:
        """Acquire a connection from the pool, returning it automatically on context exit."""
        if self._closed:
            raise RuntimeError("Connection pool is closed")

        try:
            conn = self._pool.get(block=True, timeout=timeout)
        except queue.Empty:
            raise TimeoutError("Connection acquisition timed out")

        try:
            yield conn
        finally:
            if not self._closed and conn.is_open:
                self._pool.put(conn)

    def close_all(self) -> None:
        """Close all connections and destroy the pool."""
        self._closed = True
        for conn in self._all_conns:
            conn.close()
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except queue.Empty:
                break
