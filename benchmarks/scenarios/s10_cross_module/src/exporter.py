"""Exporter module — consumer of data_serializer."""
from __future__ import annotations

from benchmarks.scenarios.s10_cross_module.src.data_serializer import serialize


def export_records(records: list[dict], fmt: str = "json") -> bytes:
    """Export records using the shared serializer."""
    return serialize(records, fmt=fmt)
