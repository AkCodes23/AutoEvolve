"""Tests for gradient descent optimization convergence."""
from benchmarks.scenarios.s25_ml_tuning_speed.src.linear_regression import train_step


def test_optimization_reduces_loss():
    x = [1.0, 2.0, 3.0, 4.0]
    y = [2.0, 4.0, 6.0, 8.0]  # true model: y = 2x + 0
    w, b = 0.0, 0.0

    initial_w, initial_b, initial_loss = train_step(x, y, w, b, lr=0.01)

    for _ in range(150):
        w, b, loss = train_step(x, y, w, b, lr=0.06)

    assert loss < initial_loss
    assert round(w, 1) == 2.0
