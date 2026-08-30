"""High-precision Fast Fourier Transform implementation."""
from __future__ import annotations

import cmath
import math
from typing import List


def fft(x: List[complex]) -> List[complex]:
    """Compute Discrete Fourier Transform of 1D array using recursive Cooley-Tukey algorithm.
    
    Array length must be a power of 2.
    """
    n = len(x)
    if n <= 1:
        return list(x)
    if (n & (n - 1)) != 0:
        # Pad to next power of 2
        next_pow2 = 1 << (n - 1).bit_length()
        padded = list(x) + [complex(0, 0)] * (next_pow2 - n)
        return fft(padded)

    even = fft(x[0::2])
    odd = fft(x[1::2])

    factor = [cmath.exp(-2j * math.pi * k / n) for k in range(n // 2)]
    
    first_half = [even[k] + factor[k] * odd[k] for k in range(n // 2)]
    second_half = [even[k] - factor[k] * odd[k] for k in range(n // 2)]
    return first_half + second_half


def ifft(X: List[complex]) -> List[complex]:
    """Compute Inverse Discrete Fourier Transform."""
    n = len(X)
    if n == 0:
        return []
    # Conjugate input, apply forward FFT, conjugate and scale result
    conjugated = [val.conjugate() for val in X]
    transformed = fft(conjugated)
    return [val.conjugate() / n for val in transformed]


def power_spectrum(x: List[complex]) -> List[float]:
    """Compute power spectral density magnitude."""
    freqs = fft(x)
    return [abs(f) ** 2 for f in freqs]
