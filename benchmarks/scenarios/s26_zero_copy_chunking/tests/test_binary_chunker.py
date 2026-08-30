"""Tests for zero-copy memoryview chunking."""
import hashlib
import tracemalloc
from benchmarks.scenarios.s26_zero_copy_chunking.src.binary_chunker import chunk_and_hash_buffer


def test_chunking_matches_direct_hash():
    data = b"A" * (1024 * 1024 * 2 + 500)  # 2MB + 500B
    chunks = list(chunk_and_hash_buffer(data, chunk_size=1024 * 1024))
    assert len(chunks) == 3

    # Verify first chunk hash matches direct slice
    expected_0 = hashlib.sha256(data[: 1024 * 1024]).hexdigest()
    assert chunks[0][1] == expected_0


def test_memoryview_does_not_duplicate_memory():
    # 5MB buffer
    data = b"X" * (5 * 1024 * 1024)
    tracemalloc.start()
    for _, h in chunk_and_hash_buffer(data, chunk_size=1024 * 1024):
        pass
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Peak memory during chunking should be strictly less than 100KB (zero duplicate buffer)
    assert peak < 100 * 1024
