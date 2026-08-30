"""Sliding window time-series aggregator."""
from __future__ import annotations

import bisect
from typing import List, Tuple


class SlidingWindowAggregator:
    """Computes streaming aggregations over a fixed sliding time window."""

    def __init__(self, window_ms: int):
        if window_ms <= 0:
            raise ValueError("window_ms must be positive")
        self.window_ms = window_ms
        # List of (timestamp_ms, value) tuples in chronological order
        self.events: List[Tuple[int, float]] = []

    def _evict_expired(self, current_time_ms: int) -> None:
        """Evict events that fall outside [current_time_ms - window_ms, current_time_ms].
        
        BUG: Off-by-one boundary eviction. Uses '<=' instead of '<', prematurely evicting
        events that are exactly on the lower boundary (current_time_ms - window_ms).
        """
        cutoff = current_time_ms - self.window_ms
        # Buggy eviction: evicts anything <= cutoff instead of strictly < cutoff
        idx = 0
        while idx < len(self.events) and self.events[idx][0] <= cutoff:
            idx += 1
        if idx > 0:
            self.events = self.events[idx:]

    def record(self, timestamp_ms: int, value: float) -> None:
        """Record an event with a millisecond timestamp and float value."""
        if not self.events or timestamp_ms >= self.events[-1][0]:
            self.events.append((timestamp_ms, float(value)))
        else:
            # Maintain sorted order if events arrive slightly out of order
            bisect.insort(self.events, (timestamp_ms, float(value)))

    def get_count(self, current_time_ms: int) -> int:
        """Return total count of active events within the window."""
        self._evict_expired(current_time_ms)
        return len(self.events)

    def get_sum(self, current_time_ms: int) -> float:
        """Return sum of values within the window."""
        self._evict_expired(current_time_ms)
        return sum(val for _, val in self.events)

    def get_average(self, current_time_ms: int) -> float:
        """Return arithmetic mean of values within the window."""
        self._evict_expired(current_time_ms)
        if not self.events:
            return 0.0
        return self.get_sum(current_time_ms) / len(self.events)

    def get_percentile(self, current_time_ms: int, percentile: float) -> float:
        """Calculate the given percentile (0 to 100) of values in the active window."""
        if not (0.0 <= percentile <= 100.0):
            raise ValueError("Percentile must be between 0.0 and 100.0")
        self._evict_expired(current_time_ms)
        if not self.events:
            return 0.0
        sorted_vals = sorted(val for _, val in self.events)
        k = (len(sorted_vals) - 1) * (percentile / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])
