"""Tests for the core serializer."""
from benchmarks.scenarios.s10_cross_module.src.data_serializer import serialize
import pytest


def test_json_default():
    result = serialize({"a": 1}, fmt="json")
    assert b'"a": 1' in result

def test_json_encoding_utf8():
    result = serialize({"emoji": "\u2764"}, fmt="json", encoding="utf-8")
    assert "\u2764".encode("utf-8") in result

def test_csv_format():
    records = [{"name": "alice", "age": "30"}, {"name": "bob", "age": "25"}]
    result = serialize(records, fmt="csv")
    assert b"alice" in result
    assert b"bob" in result

def test_unsupported_format():
    with pytest.raises(ValueError, match="[Uu]nsupported"):
        serialize({}, fmt="xml")

def test_backward_compat_no_encoding_arg():
    result = serialize({"x": 1})
    assert isinstance(result, bytes)
