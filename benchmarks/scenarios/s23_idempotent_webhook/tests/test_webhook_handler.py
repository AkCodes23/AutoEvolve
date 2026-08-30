"""Tests for idempotent webhook processing."""
from benchmarks.scenarios.s23_idempotent_webhook.src.webhook_handler import PaymentLedger


def test_first_event_applies_balance():
    ledger = PaymentLedger()
    res = ledger.process_webhook("evt_1001", "acc_1", 50.0)
    assert res is True
    assert ledger.get_balance("acc_1") == 50.0


def test_duplicate_event_is_idempotent_and_does_not_double_credit():
    ledger = PaymentLedger()
    ledger.process_webhook("evt_1001", "acc_1", 50.0)

    # Replay identical event
    res = ledger.process_webhook("evt_1001", "acc_1", 50.0)
    assert res is False
    # Balance must remain exactly 50.0, not 100.0
    assert ledger.get_balance("acc_1") == 50.0
