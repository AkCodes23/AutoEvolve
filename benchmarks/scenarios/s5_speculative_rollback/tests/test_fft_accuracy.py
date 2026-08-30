import cmath
import math
import random
import pytest
from benchmarks.scenarios.s5_speculative_rollback.src.numeric.fast_fourier import (
    fft,
    ifft,
    power_spectrum,
)


def test_impulse_response():
    # An impulse at t=0 has flat spectrum
    x = [complex(1, 0), complex(0, 0), complex(0, 0), complex(0, 0)]
    X = fft(x)
    for freq in X:
        assert abs(freq - complex(1, 0)) < 1e-7


def test_roundtrip_reconstruction_accuracy():
    # Random signal roundtrip reconstruction
    random.seed(42)
    signal = [complex(random.uniform(-10.0, 10.0), random.uniform(-10.0, 10.0)) for _ in range(64)]
    
    transformed = fft(signal)
    reconstructed = ifft(transformed)

    assert len(reconstructed) == len(signal)
    for orig, rec in zip(signal, reconstructed):
        diff = abs(orig - rec)
        assert diff < 1e-7, f"Reconstruction error {diff} exceeded tolerance 1e-7"


def test_parsevals_theorem():
    # Energy in time domain equals energy in frequency domain / N
    signal = [complex(math.sin(2 * math.pi * i / 16), 0) for i in range(16)]
    time_energy = sum(abs(x) ** 2 for x in signal)

    freq = fft(signal)
    freq_energy = sum(abs(X) ** 2 for X in freq) / len(signal)

    assert abs(time_energy - freq_energy) < 1e-7


def test_power_spectrum_positivity():
    signal = [complex(i, i * 0.5) for i in range(8)]
    ps = power_spectrum(signal)
    assert len(ps) == 8
    for p in ps:
        assert p >= 0.0
