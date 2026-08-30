"""Tests verifying correctness and strict memory boundaries for log stream analyzer."""
import tracemalloc
import pytest

from benchmarks.scenarios.s16_streaming_memory.src.log_analyzer import analyze_stream


def generate_log_stream(count: int):
    """Generator simulating 100,000 log records yielded on-the-fly."""
    for i in range(count):
        status = 500 if (i % 20 == 0) else 200
        latency = 10.0 + (i % 100)
        yield f"2026-08-15T00:00:00Z {status} {latency}"


def test_basic_stream_metrics():
    sample = [
        "2026-08-15T00:00:00Z 200 10.0",
        "2026-08-15T00:00:01Z 200 20.0",
        "2026-08-15T00:00:02Z 500 30.0",
        "2026-08-15T00:00:03Z 200 40.0",
    ]
    res = analyze_stream(iter(sample))
    assert res["total_requests"] == 4.0
    assert res["error_rate"] == 0.25
    assert res["avg_latency_ms"] == 25.0
    assert res["max_latency_ms"] == 40.0


def test_streaming_memory_bound():
    """Verify that processing 100,000 log records does not exceed 1MB peak RAM."""
    tracemalloc.start()
    stream = generate_log_stream(100_000)
    res = analyze_stream(stream)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert res["total_requests"] == 100_000.0
    # Peak memory must be strictly under 1MB (1,048,576 bytes)
    assert peak < 1_048_576, f"Memory peak {peak} bytes exceeded 1MB bound"
