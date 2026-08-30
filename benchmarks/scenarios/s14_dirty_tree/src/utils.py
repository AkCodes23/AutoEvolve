"""Utility module with a bug to fix — agent must not touch other files."""
from __future__ import annotations

from typing import Any


def flatten(nested: list[Any], max_depth: int = -1) -> list[Any]:
    """Flatten a nested list structure.

    Args:
        nested: A potentially nested list.
        max_depth: Maximum recursion depth (-1 for unlimited).

    Returns:
        Flattened list.
    """
    result = []

    def _walk(items: list, depth: int) -> None:
        for item in items:
            if isinstance(item, list) and (max_depth < 0 or depth < max_depth):
                _walk(item, depth + 1)
            else:
                result.append(item)

    _walk(nested, 0)
    return result


def deduplicate(items: list[Any], preserve_order: bool = True) -> list[Any]:
    """Remove duplicates from a list.

    Args:
        items: Input list.
        preserve_order: If True, maintains first-occurrence order.

    Returns:
        List with duplicates removed.
    """
    if preserve_order:
        seen = set()
        result = []
        for item in items:
            key = item if isinstance(item, (int, float, str, bool, type(None))) else id(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
    return list(set(items))


def chunk(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list into chunks of the given size.

    Args:
        items: Input list.
        size: Chunk size.

    Returns:
        List of chunks.

    Raises:
        ValueError: If size is not positive.
    """
    if size <= 0:
        raise ValueError(f"Chunk size must be positive, got {size}")
    return [items[i : i + size] for i in range(0, len(items), size)]
