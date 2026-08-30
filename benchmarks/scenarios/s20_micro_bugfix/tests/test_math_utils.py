"""Tests for math utils."""
from benchmarks.scenarios.s20_micro_bugfix.src.math_utils import subtract


def test_subtract():
    assert subtract(10, 3) == 7.0
    assert subtract(5, 5) == 0.0
    assert subtract(0, 5) == -5.0
