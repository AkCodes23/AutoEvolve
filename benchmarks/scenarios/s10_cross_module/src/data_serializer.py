"""Data serializer with encoding support — shared across 3 consumers."""
from __future__ import annotations

import json
from typing import Any


def serialize(obj: Any, fmt: str = "json", encoding: str = "utf-8") -> bytes:
    """Serialize an object to bytes.

    Args:
        obj: The object to serialize.
        fmt: Output format ('json' or 'csv').
        encoding: Character encoding for the output bytes.

    Returns:
        Serialized bytes.

    Raises:
        ValueError: For unsupported formats.
    """
    if fmt == "json":
        text = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    elif fmt == "csv":
        if isinstance(obj, list) and all(isinstance(r, dict) for r in obj):
            if not obj:
                return b""
            keys = sorted(obj[0].keys())
            lines = [",".join(keys)]
            for row in obj:
                lines.append(",".join(str(row.get(k, "")) for k in keys))
            text = "\n".join(lines)
        else:
            raise ValueError("CSV format requires a list of dicts.")
    else:
        raise ValueError(f"Unsupported format: {fmt!r}")

    return text.encode(encoding)
