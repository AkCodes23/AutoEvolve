"""Tests for ACID transaction rollback behavior."""
import pytest
from benchmarks.scenarios.s32_acid_transaction.src.transaction_scope import DatabaseStore


def test_successful_transaction_commits():
    db = DatabaseStore()
    db.set("balance_a", 100)
    db.set("balance_b", 50)

    with db.transaction():
        db.set("balance_a", 80)
        db.set("balance_b", 70)

    assert db.get("balance_a") == 80
    assert db.get("balance_b") == 70


def test_failed_transaction_rolls_back_entirely():
    db = DatabaseStore()
    db.set("balance_a", 100)
    db.set("balance_b", 50)

    with pytest.raises(RuntimeError, match="mid-mutation crash"):
        with db.transaction():
            db.set("balance_a", 80)
            raise RuntimeError("mid-mutation crash")

    # balance_a must be rolled back to 100
    assert db.get("balance_a") == 100
    assert db.get("balance_b") == 50
