"""File processor that reads and processes files from user-specified directories."""
from __future__ import annotations

import os


ALLOWED_BASE = os.path.join(os.path.dirname(__file__), "data")


def read_file(base_dir: str, filename: str) -> str:
    """Read a file from the given directory.

    Args:
        base_dir: Base directory to read from.
        filename: Name of the file to read.

    Returns:
        File contents as a string.

    Raises:
        ValueError: If the resolved path escapes the allowed base directory.
        FileNotFoundError: If the file does not exist.
    """
    safe_base = os.path.realpath(base_dir)
    requested = os.path.realpath(os.path.join(safe_base, filename))

    if not requested.startswith(safe_base + os.sep) and requested != safe_base:
        raise ValueError(
            f"Path traversal blocked: {filename!r} resolves outside {base_dir!r}"
        )

    if not os.path.isfile(requested):
        raise FileNotFoundError(f"No such file: {requested}")

    with open(requested, "r", encoding="utf-8") as f:
        return f.read()


def list_files(base_dir: str) -> list[str]:
    """List files in a directory without following symlinks outside the boundary."""
    safe_base = os.path.realpath(base_dir)
    results = []
    for entry in os.listdir(safe_base):
        full = os.path.join(safe_base, entry)
        real = os.path.realpath(full)
        if real.startswith(safe_base + os.sep) and os.path.isfile(real):
            results.append(entry)
    return sorted(results)


def process_file(base_dir: str, filename: str) -> dict:
    """Read and compute basic stats for a file."""
    content = read_file(base_dir, filename)
    lines = content.splitlines()
    return {
        "filename": filename,
        "size_bytes": len(content.encode("utf-8")),
        "line_count": len(lines),
        "word_count": sum(len(line.split()) for line in lines),
    }
