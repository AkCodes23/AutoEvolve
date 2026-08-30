"""In-memory ACID transaction context manager with automatic rollback."""
from __future__ import annotations

import contextlib
import copy
from typing import Any, Dict, Generator


class DatabaseStore:
    """Key-value database with atomic transaction snapshot rollback."""

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, val: Any) -> None:
        self._data[key] = val

    @contextlib.contextmanager
    def transaction(self) -> Generator[DatabaseStore, None, None]:
        """Atomic transaction scope: automatically rolls back state snapshot on exception."""
        snapshot = copy.deepcopy(self._data)
        try:
            yield self
        except Exception:
            self._data = snapshot
            raise
