import pytest
from benchmarks.scenarios.s1_blast_radius.src.utils.url_builder import build_query_url


def test_empty_params():
    assert build_query_url("https://example.com/api", {}) == "https://example.com/api"


def test_single_scalar_param():
    url = build_query_url("https://example.com/api", {"user": "alice"})
    assert url == "https://example.com/api?user=alice"


def test_multiple_sorted_scalar_params():
    url = build_query_url("https://example.com/api", {"z": "last", "a": "first"}, sort_keys=True)
    assert url == "https://example.com/api?a=first&z=last"


def test_existing_query_string_delimiter():
    url = build_query_url("https://example.com/api?existing=1", {"user": "bob"})
    assert url == "https://example.com/api?existing=1&user=bob"


def test_list_and_tuple_multi_value_params():
    url = build_query_url(
        "https://example.com/api",
        {"status": ["active", "pending"], "type": ("user", "admin")},
        sort_keys=True
    )
    # Expected: repeated query parameter keys
    assert url == "https://example.com/api?status=active&status=pending&type=user&type=admin"


def test_empty_list_param():
    url = build_query_url("https://example.com/api", {"status": []})
    assert url == "https://example.com/api"
