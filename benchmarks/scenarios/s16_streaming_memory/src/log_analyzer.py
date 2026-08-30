"""Streaming log analyzer processing arbitrary line streams in O(1) space."""
from __future__ import annotations

import heapq
from typing import Dict, Iterator, Tuple


def analyze_stream(lines: Iterator[str]) -> Dict[str, float]:
    """Analyze a stream of log records and calculate metrics without buffering lines into RAM.
    
    Each line format: "<timestamp> <status_code> <response_time_ms>"
    """
    total_count = 0
    error_count = 0
    total_latency = 0.0
    max_latency = 0.0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue

        try:
            status = int(parts[1])
            latency = float(parts[2])
        except ValueError:
            continue

        total_count += 1
        total_latency += latency
        if latency > max_latency:
            max_latency = latency
        if status >= 500:
            error_count += 1

    avg_latency = (total_latency / total_count) if total_count > 0 else 0.0
    error_rate = (error_count / total_count) if total_count > 0 else 0.0

    return {
        "total_requests": float(total_count),
        "error_rate": round(error_rate, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "max_latency_ms": round(max_latency, 2),
    }
