"""Idempotent payment webhook consumer with deduplication store."""
from __future__ import annotations

from typing import Dict, Set


class PaymentLedger:
    """Ledger processing payments with strict idempotency key checks."""

    def __init__(self):
        self._processed_keys: Set[str] = set()
        self._balances: Dict[str, float] = {}

    def process_webhook(self, event_id: str, account_id: str, amount: float) -> bool:
        """Process incoming payment webhook. Returns True if applied, False if duplicate."""
        if not event_id or not account_id:
            raise ValueError("event_id and account_id required")
        if amount <= 0:
            raise ValueError("amount must be positive")

        if event_id in self._processed_keys:
            # Idempotent return without re-applying balance
            return False

        self._balances[account_id] = self._balances.get(account_id, 0.0) + amount
        self._processed_keys.add(event_id)
        return True

    def get_balance(self, account_id: str) -> float:
        return self._balances.get(account_id, 0.0)
