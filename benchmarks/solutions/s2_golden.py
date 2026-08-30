"""Golden implementation for Scenario 2: Sliding Window Aggregator."""
from __future__ import annotations

import bisect
from typing import List, Tuple


class SlidingWindowAggregator:
    """Computes streaming aggregations over a fixed sliding time window with exact boundary inclusion."""

    def __init__(self, window_ms: int):
        if window_ms <= 0:
            raise ValueError("window_ms must be positive")
        self.window_ms = window_ms
        self.events: List[Tuple[int, float]] = []

    def _evict_expired(self, current_time_ms: int) -> None:
        """Evict events strictly older than current_time_ms - window_ms."""
        cutoff = current_time_ms - self.window_ms
        idx = 0
        while idx < len(self.events) and self.events[idx][0] < cutoff:
            idx += 1
        if idx > 0:
            self.events = self.events[idx:]

    def _active_values(self, current_time_ms: int) -> List[float]:
        self._evict_expired(current_time_ms)
        return [val for ts, val in self.events if ts <= current_time_ms]

    def record(self, timestamp_ms: int, value: float) -> None:
        """Record an event with a millisecond timestamp and float value."""
        if not self.events or timestamp_ms >= self.events[-1][0]:
            self.events.append((timestamp_ms, float(value)))
        else:
            bisect.insort(self.events, (timestamp_ms, float(value)))

    def get_count(self, current_time_ms: int) -> int:
        """Return total count of active events within the window [now - window_ms, now]."""
        return len(self._active_values(current_time_ms))

    def get_sum(self, current_time_ms: int) -> float:
        """Return sum of values within the active window."""
        return sum(self._active_values(current_time_ms))

    def get_average(self, current_time_ms: int) -> float:
        """Return arithmetic mean of values within the active window."""
        vals = self._active_values(current_time_ms)
        if not vals:
            return 0.0
        return sum(vals) / len(vals)

    def get_percentile(self, current_time_ms: int, percentile: float) -> float:
        """Calculate the given percentile (0 to 100) of values in the active window."""
        if not (0.0 <= percentile <= 100.0):
            raise ValueError("Percentile must be between 0.0 and 100.0")
        vals = self._active_values(current_time_ms)
        if not vals:
            return 0.0
        sorted_vals = sorted(vals)
        k = (len(sorted_vals) - 1) * (percentile / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])
