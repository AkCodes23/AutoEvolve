"""Tests for legacy formatter — backward compat + new JSON feature."""
from __future__ import annotations

import json

import pytest

from benchmarks.scenarios.s11_backward_compat.src.legacy_formatter import (
    format_record,
    format_records,
)


class TestPlainStyleRegression:
    """These tests MUST continue to pass exactly as they did before JSON was added."""

    def test_plain_is_default(self):
        result = format_record({"name": "alice", "age": 30})
        assert "name: alice" in result
        assert "age: 30" in result

    def test_plain_sorted_keys(self):
        result = format_record({"z": 1, "a": 2})
        lines = result.strip().split("\n")
        assert lines[0].startswith("a:")
        assert lines[1].startswith("z:")

    def test_plain_exact_format(self):
        result = format_record({"key": "value"})
        assert result == "key: value"

    def test_plain_multiple_records(self):
        result = format_records([{"a": 1}, {"b": 2}])
        assert "a: 1" in result
        assert "b: 2" in result
        assert "\n\n" in result

    def test_default_style_is_plain_not_json(self):
        result = format_record({"x": 1})
        assert result == "x: 1"
        assert "{" not in result


class TestJsonStyleNew:
    def test_json_valid(self):
        result = format_record({"name": "alice"}, style="json")
        parsed = json.loads(result)
        assert parsed["name"] == "alice"

    def test_json_sorted_keys(self):
        result = format_record({"z": 1, "a": 2}, style="json")
        parsed = json.loads(result)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_json_multiple_records(self):
        result = format_records([{"a": 1}], style="json")
        parsed = json.loads(result)
        assert parsed["a"] == 1


class TestErrorHandling:
    def test_unsupported_style_raises(self):
        with pytest.raises(ValueError, match="[Uu]nsupported"):
            format_record({"x": 1}, style="xml")
