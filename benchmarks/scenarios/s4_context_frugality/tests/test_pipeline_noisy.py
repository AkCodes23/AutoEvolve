import sys
import pytest
from benchmarks.scenarios.s4_context_frugality.src.pipeline.transformer import DataTransformer


def test_chunk_ingestion_simulation():
    # Simulates noisy ingestion log traffic
    for chunk_id in range(6000):
        sys.stdout.write(f"[DEBUG 2026-08-14 10:00:{chunk_id % 60:02d}.{chunk_id % 1000:03d}] Ingesting chunk {chunk_id}/6000: payload_bytes=4096 stream_id=0x{chunk_id:04x} status=OK\n")
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    mean, std = DataTransformer.compute_stats(data)
    assert mean == 3.0
    assert abs(std - 1.5811388) < 1e-5


def test_batch_processing_trace_logs():
    # Simulates socket trace logs
    for trace_id in range(6000):
        sys.stdout.write(f"[TRACE 2026-08-14 10:01:{trace_id % 60:02d}.{trace_id % 1000:03d}] Socket event: FD={100 + (trace_id % 20)} RX=1024 TX=1024 TLS_SESSION=active latency_us=124\n")
    clipped = DataTransformer.clip_bounds([-10.0, 0.0, 5.0, 15.0], min_val=-2.0, max_val=10.0)
    assert clipped == [-2.0, 0.0, 5.0, 10.0]


def test_scale_normalization():
    # Subtle mathematical scaling assertion
    dataset = [10.0, 20.0, 30.0, 40.0, 50.0]
    normalized = DataTransformer.normalize_scale(dataset, target_mean=0.0, target_std=1.0)
    
    mean, std = DataTransformer.compute_stats(normalized)
    assert abs(mean - 0.0) < 1e-6, f"Expected mean 0.0, got {mean}"
    # This assertion fails because of the 1.005 factor: std will be ~0.995024 instead of 1.0
    assert abs(std - 1.0) < 1e-6, f"Expected std 1.0, got {std}"
