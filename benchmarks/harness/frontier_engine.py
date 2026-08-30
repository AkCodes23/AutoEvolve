"""Continuous Non-Saturated Evaluation Engine for AutoEvolve SWE Benchmarks.

Provides continuous (non-binary) multi-metric grading:
- Correctness Rate (0.0 to 1.0) via property-based fuzzing and edge cases
- Latency Efficiency Score (0.0 to 1.0) scaled against theoretical optimal
- Memory Boundedness Score (0.0 to 1.0) scaled against RSS ceilings
- Concurrency & Race Condition Safety (0.0 to 1.0)
- Architectural Brevity & YAGNI Score (0.0 to 1.0)
"""
from __future__ import annotations

import math
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple


def calculate_continuous_score(
    *,
    correctness_rate: float,
    actual_latency_ms: float,
    target_latency_ms: float,
    actual_memory_kb: float,
    target_memory_kb: float,
    actual_loc: int,
    golden_loc: int,
    concurrency_errors: int = 0,
    weight_correctness: float = 0.40,
    weight_latency: float = 0.20,
    weight_memory: float = 0.20,
    weight_brevity: float = 0.10,
    weight_safety: float = 0.10,
) -> Dict[str, Any]:
    """Compute continuous, non-saturated score in [0.0, 100.0]."""
    # 1. Correctness: non-linear steep drop if basic correctness fails
    c_score = max(0.0, min(1.0, correctness_rate))

    # 2. Latency efficiency: logarithmic scaling around target
    if actual_latency_ms <= 0:
        lat_score = 1.0
    else:
        ratio = target_latency_ms / max(actual_latency_ms, 0.001)
        lat_score = max(0.0, min(1.0, ratio if ratio <= 1.0 else 1.0 + 0.1 * math.log(ratio)))

    # 3. Memory boundedness
    if actual_memory_kb <= target_memory_kb:
        mem_score = 1.0
    else:
        # Penalize memory blowup
        overage = actual_memory_kb / max(target_memory_kb, 1.0)
        mem_score = max(0.0, 1.0 / overage)

    # 4. Brevity / YAGNI
    if actual_loc <= golden_loc:
        brevity_score = 1.0
    else:
        brevity_score = max(0.0, 1.0 - ((actual_loc - golden_loc) / max(golden_loc * 2, 10)))

    # 5. Concurrency safety
    safety_score = max(0.0, 1.0 - (concurrency_errors * 0.25))

    # If correctness is below 0.5, scale down all scores
    gate_factor = c_score if c_score < 0.5 else 1.0

    raw_composite = (
        (c_score * weight_correctness)
        + (lat_score * weight_latency)
        + (mem_score * weight_memory)
        + (brevity_score * weight_brevity)
        + (safety_score * weight_safety)
    ) * gate_factor

    final_score = round(max(0.0, min(100.0, raw_composite * 100.0)), 2)

    return {
        "score": final_score,
        "correctness_score": round(c_score * 100.0, 2),
        "latency_score": round(lat_score * 100.0, 2),
        "memory_score": round(mem_score * 100.0, 2),
        "brevity_score": round(brevity_score * 100.0, 2),
        "safety_score": round(safety_score * 100.0, 2),
        "metrics": {
            "correctness_rate": correctness_rate,
            "actual_latency_ms": actual_latency_ms,
            "target_latency_ms": target_latency_ms,
            "actual_memory_kb": actual_memory_kb,
            "target_memory_kb": target_memory_kb,
            "actual_loc": actual_loc,
            "golden_loc": golden_loc,
            "concurrency_errors": concurrency_errors,
        },
    }
