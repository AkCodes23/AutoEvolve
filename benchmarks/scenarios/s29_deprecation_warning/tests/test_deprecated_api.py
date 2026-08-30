"""Tests for graceful API deprecation warnings."""
import pytest
from benchmarks.scenarios.s29_deprecation_warning.src.deprecated_api import get_all_users, fetch_users_v2


def test_v2_call_works():
    assert fetch_users_v2(filter_active=True) == ["alice", "bob"]


def test_legacy_call_emits_deprecation_warning_and_returns_valid_data():
    with pytest.deprecated_call():
        users = get_all_users()
    assert users == ["alice", "bob", "charlie"]
