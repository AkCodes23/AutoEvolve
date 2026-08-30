"""Zero-copy binary chunker using memoryview."""
from __future__ import annotations

import hashlib
from typing import Generator, Tuple


def chunk_and_hash_buffer(data: bytes, chunk_size: int = 1024 * 1024) -> Generator[Tuple[int, str], None, None]:
    """Yield (chunk_index, sha256_hex) using zero-copy memoryview slices."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    view = memoryview(data)
    total_len = len(view)

    for i in range(0, total_len, chunk_size):
        chunk_view = view[i : min(i + chunk_size, total_len)]
        chunk_hash = hashlib.sha256(chunk_view).hexdigest()
        yield (i // chunk_size, chunk_hash)
