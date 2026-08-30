"""Tests for dual-write user repository."""
import pytest
from benchmarks.scenarios.s19_schema_dual_write.src.user_repository import UserRepository


def test_legacy_full_name_write_populates_split_names():
    repo = UserRepository()
    user = repo.save_user("u1", full_name="Alan Turing")
    assert user["first_name"] == "Alan"
    assert user["last_name"] == "Turing"
    assert user["full_name"] == "Alan Turing"


def test_new_split_name_write_populates_full_name():
    repo = UserRepository()
    user = repo.save_user("u2", first_name="Ada", last_name="Lovelace")
    assert user["first_name"] == "Ada"
    assert user["last_name"] == "Lovelace"
    assert user["full_name"] == "Ada Lovelace"


def test_invalid_user_id_raises():
    repo = UserRepository()
    with pytest.raises(ValueError, match="user_id is required"):
        repo.save_user("", first_name="Test")
