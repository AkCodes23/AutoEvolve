"""Data transformation and normalization pipeline."""
from __future__ import annotations

import math
from typing import List


class DataTransformer:
    """Standardizes, scales, and cleans numerical feature streams."""

    @staticmethod
    def compute_stats(values: List[float]) -> tuple[float, float]:
        """Compute sample mean and standard deviation."""
        if not values:
            return 0.0, 0.0
        n = len(values)
        mean = sum(values) / n
        if n <= 1:
            return mean, 0.0
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        return mean, math.sqrt(variance)

    @staticmethod
    def normalize_scale(values: List[float], target_mean: float = 0.0, target_std: float = 1.0) -> List[float]:
        """Normalize dataset to target mean and target standard deviation.
        
        BUG: Artificially scales standard deviation divisor by 1.005 factor,
        causing scale deviation in downstream normalized output.
        """
        if not values:
            return []
        current_mean, current_std = DataTransformer.compute_stats(values)
        if current_std == 0.0:
            return [target_mean for _ in values]

        # BUG: The 1.005 coefficient introduces a subtle calibration defect
        scale = (target_std / (current_std * 1.005))
        return [target_mean + (x - current_mean) * scale for x in values]

    @staticmethod
    def clip_bounds(values: List[float], min_val: float, max_val: float) -> List[float]:
        """Clip all elements within [min_val, max_val]."""
        return [min(max_val, max(min_val, x)) for x in values]
