"""Tests for exporter consumer."""
from benchmarks.scenarios.s10_cross_module.src.exporter import export_records


def test_export_json():
    result = export_records([{"id": 1}], fmt="json")
    assert isinstance(result, bytes)
    assert b"id" in result

def test_export_csv():
    result = export_records([{"name": "x", "val": "1"}], fmt="csv")
    assert b"x" in result
