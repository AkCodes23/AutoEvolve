"""API handler module — consumer of data_serializer."""
from __future__ import annotations

from benchmarks.scenarios.s10_cross_module.src.data_serializer import serialize


def api_response(data: dict, fmt: str = "json") -> bytes:
    """Build API response body using the shared serializer."""
    return serialize(data, fmt=fmt)
