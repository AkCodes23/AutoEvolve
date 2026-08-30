"""Tests for cache manager consumer."""
from benchmarks.scenarios.s10_cross_module.src.cache_manager import cache_entry


def test_cache_entry_serializes():
    result = cache_entry("user:1", {"name": "alice"})
    assert isinstance(result, bytes)
    assert b"alice" in result
    assert b"user:1" in result
