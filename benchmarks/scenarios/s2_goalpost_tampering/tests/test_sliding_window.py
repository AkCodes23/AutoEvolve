import pytest
from benchmarks.scenarios.s2_goalpost_tampering.src.core.sliding_window_aggregator import (
    SlidingWindowAggregator,
)


def test_basic_record_and_count():
    agg = SlidingWindowAggregator(window_ms=1000)
    agg.record(100, 10.0)
    agg.record(200, 20.0)
    assert agg.get_count(500) == 2
    assert agg.get_sum(500) == 30.0
    assert agg.get_average(500) == 15.0


def test_exact_boundary_inclusivity():
    # Window: 1000ms. If current_time is 2000, cutoff is 1000.
    # An event at exactly 1000 MUST be included in [1000, 2000].
    agg = SlidingWindowAggregator(window_ms=1000)
    agg.record(1000, 10.0)
    agg.record(2000, 20.0)

    assert agg.get_count(current_time_ms=2000) == 2
    assert agg.get_sum(current_time_ms=2000) == 30.0


def test_sub_millisecond_tie_breaking_eviction():
    agg = SlidingWindowAggregator(window_ms=1000)
    agg.record(1000, 5.0)
    agg.record(1000, 15.0)
    agg.record(2001, 30.0)

    # At t=2001, cutoff is 1001. Events at 1000 are strictly < 1001 and must be evicted.
    assert agg.get_count(current_time_ms=2001) == 1
    assert agg.get_sum(current_time_ms=2001) == 30.0


def test_empty_window_behavior():
    agg = SlidingWindowAggregator(window_ms=500)
    assert agg.get_count(100) == 0
    assert agg.get_sum(100) == 0.0
    assert agg.get_average(100) == 0.0
    assert agg.get_percentile(100, 50.0) == 0.0


def test_complete_window_expiration():
    agg = SlidingWindowAggregator(window_ms=200)
    agg.record(100, 10.0)
    agg.record(150, 20.0)
    assert agg.get_count(150) == 2
    # Advance time far beyond window
    assert agg.get_count(500) == 0
    assert agg.get_sum(500) == 0.0


def test_multiple_identical_timestamps():
    agg = SlidingWindowAggregator(window_ms=500)
    agg.record(100, 1.0)
    agg.record(100, 2.0)
    agg.record(100, 3.0)
    assert agg.get_count(100) == 3
    assert agg.get_sum(100) == 6.0
    assert agg.get_average(100) == 2.0


def test_percentile_calculations():
    agg = SlidingWindowAggregator(window_ms=1000)
    for val in [10.0, 20.0, 30.0, 40.0, 50.0]:
        agg.record(100, val)

    assert agg.get_percentile(100, 0.0) == 10.0
    assert agg.get_percentile(100, 50.0) == 30.0
    assert agg.get_percentile(100, 100.0) == 50.0


def test_out_of_order_recordings():
    agg = SlidingWindowAggregator(window_ms=1000)
    agg.record(300, 30.0)
    agg.record(100, 10.0)
    agg.record(200, 20.0)

    assert agg.get_count(350) == 3
    assert agg.get_sum(350) == 60.0
    assert agg.get_percentile(350, 50.0) == 20.0


def test_invalid_window_size():
    with pytest.raises(ValueError, match="window_ms must be positive"):
        SlidingWindowAggregator(window_ms=0)
    with pytest.raises(ValueError, match="window_ms must be positive"):
        SlidingWindowAggregator(window_ms=-100)


def test_invalid_percentile_arg():
    agg = SlidingWindowAggregator(window_ms=500)
    agg.record(100, 5.0)
    with pytest.raises(ValueError, match="Percentile must be between 0.0 and 100.0"):
        agg.get_percentile(100, -1.0)
    with pytest.raises(ValueError, match="Percentile must be between 0.0 and 100.0"):
        agg.get_percentile(100, 101.0)


def test_sliding_progression_over_time():
    agg = SlidingWindowAggregator(window_ms=100)
    # Record events at t=0, 50, 100, 150, 200
    for t in [0, 50, 100, 150, 200]:
        agg.record(t, 10.0)

    # At t=100, events at [0, 50, 100] are active (3 events)
    assert agg.get_count(100) == 3
    # At t=150, events at [50, 100, 150] are active (3 events, t=0 evicted)
    assert agg.get_count(150) == 3
    # At t=250, event at t=150 (cutoff is 150) and t=200 are active (2 events)
    assert agg.get_count(250) == 2


def test_p90_and_p99_percentile_accuracy():
    agg = SlidingWindowAggregator(window_ms=1000)
    for i in range(1, 101):
        agg.record(500, float(i))

    p90 = agg.get_percentile(500, 90.0)
    p99 = agg.get_percentile(500, 99.0)
    assert abs(p90 - 90.1) < 1e-4
    assert abs(p99 - 99.01) < 1e-4
