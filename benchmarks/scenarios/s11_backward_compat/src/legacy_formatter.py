"""Legacy record formatter with backward-compatible JSON support."""
from __future__ import annotations

import json
from typing import Any


def format_record(data: dict[str, Any], style: str = "plain") -> str:
    """Format a data record for display or export.

    Args:
        data: Key-value pairs to format.
        style: Output style — 'plain' (legacy default) or 'json'.

    Returns:
        Formatted string.

    Raises:
        ValueError: For unsupported styles.
    """
    if style == "plain":
        lines = []
        for key in sorted(data.keys()):
            lines.append(f"{key}: {data[key]}")
        return "\n".join(lines)
    elif style == "json":
        return json.dumps(data, sort_keys=True, indent=2)
    else:
        raise ValueError(f"Unsupported style: {style!r}")


def format_records(records: list[dict[str, Any]], style: str = "plain") -> str:
    """Format multiple records, separated by blank lines."""
    return "\n\n".join(format_record(r, style=style) for r in records)
