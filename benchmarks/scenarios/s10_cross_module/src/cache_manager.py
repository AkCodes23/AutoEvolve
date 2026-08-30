"""Cache manager module — consumer of data_serializer."""
from __future__ import annotations

from benchmarks.scenarios.s10_cross_module.src.data_serializer import serialize


def cache_entry(key: str, value: dict) -> bytes:
    """Serialize a cache entry using the shared serializer."""
    return serialize({"key": key, "value": value}, fmt="json")
