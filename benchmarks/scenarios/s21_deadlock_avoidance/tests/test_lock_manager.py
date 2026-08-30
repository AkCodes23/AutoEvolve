"""Tests verifying deadlock-free concurrent multi-resource locking."""
import threading
from benchmarks.scenarios.s21_deadlock_avoidance.src.lock_manager import Account, transfer_funds


def test_concurrent_bidirectional_transfers():
    """Verify that 20 threads transferring bidirectionally between A and B do not deadlock."""
    acc_a = Account("acc_A", 1000.0)
    acc_b = Account("acc_B", 1000.0)

    threads = []
    for i in range(10):
        t1 = threading.Thread(target=lambda: transfer_funds(acc_a, acc_b, 10.0))
        t2 = threading.Thread(target=lambda: transfer_funds(acc_b, acc_a, 10.0))
        threads.extend([t1, t2])

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2.0)
        assert not t.is_alive(), "Thread deadlocked during concurrent transfer"

    assert acc_a.balance + acc_b.balance == 2000.0
