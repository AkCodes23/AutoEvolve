"""Thread-safe multi-resource lock manager preventing circular deadlocks."""
from __future__ import annotations

import contextlib
import threading
from typing import Generator, List


class Account:
    def __init__(self, account_id: str, balance: float):
        self.account_id = account_id
        self.balance = balance
        self._lock = threading.Lock()


@contextlib.contextmanager
def acquire_ordered_locks(accounts: List[Account]) -> Generator[None, None, None]:
    """Acquire locks in deterministic sorted order by account_id to eliminate circular wait."""
    sorted_accounts = sorted(accounts, key=lambda a: a.account_id)
    acquired = []
    try:
        for acc in sorted_accounts:
            acc._lock.acquire()
            acquired.append(acc)
        yield
    finally:
        for acc in reversed(acquired):
            acc._lock.release()


def transfer_funds(src: Account, dst: Account, amount: float) -> bool:
    """Transfer funds between accounts safely without deadlock."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    with acquire_ordered_locks([src, dst]):
        if src.balance < amount:
            return False
        src.balance -= amount
        dst.balance += amount
        return True
