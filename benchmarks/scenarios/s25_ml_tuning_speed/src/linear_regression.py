"""Minimal gradient descent model optimization."""
from __future__ import annotations

from typing import List, Tuple


def train_step(x: List[float], y: List[float], w: float, b: float, lr: float) -> Tuple[float, float, float]:
    """Single gradient descent optimization step returning (new_w, new_b, loss)."""
    n = len(x)
    dw = 0.0
    db = 0.0
    total_loss = 0.0

    for i in range(n):
        pred = w * x[i] + b
        diff = pred - y[i]
        total_loss += diff ** 2
        dw += (2 / n) * diff * x[i]
        db += (2 / n) * diff

    mse_loss = total_loss / n
    new_w = w - lr * dw
    new_b = b - lr * db
    return new_w, new_b, mse_loss
