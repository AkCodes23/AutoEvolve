"""Tests for API handler consumer."""
from benchmarks.scenarios.s10_cross_module.src.api_handler import api_response


def test_api_response_json():
    result = api_response({"status": "ok"}, fmt="json")
    assert isinstance(result, bytes)
    assert b"ok" in result
