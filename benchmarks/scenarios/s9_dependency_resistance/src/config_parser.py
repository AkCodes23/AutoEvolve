"""TOML-like configuration parser using only standard library."""
from __future__ import annotations

import re
from typing import Any


def parse_toml(text: str) -> dict[str, Any]:
    """Parse a simple TOML configuration string into a dict.

    Supports:
        - [section] headers
        - key = "string_value"
        - key = 123 (integers)
        - key = 1.5 (floats)
        - key = true/false (booleans)
        - # comments

    Returns:
        Nested dict with section keys mapping to their key-value pairs.
    """
    result: dict[str, Any] = {}
    current_section: dict[str, Any] = result
    section_name = ""

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        section_match = re.match(r"^\[([a-zA-Z0-9_.\-]+)\]$", line)
        if section_match:
            section_name = section_match.group(1)
            if section_name not in result:
                result[section_name] = {}
            current_section = result[section_name]
            continue

        kv_match = re.match(r'^([a-zA-Z0-9_\-]+)\s*=\s*(.+)$', line)
        if not kv_match:
            raise ValueError(f"Line {lineno}: invalid syntax: {raw_line!r}")

        key = kv_match.group(1)
        raw_value = kv_match.group(2).strip()

        current_section[key] = _parse_value(raw_value, lineno)

    return result


def _parse_value(raw: str, lineno: int) -> Any:
    """Parse a single TOML value."""
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False

    try:
        return int(raw)
    except ValueError:
        pass

    try:
        return float(raw)
    except ValueError:
        pass

    raise ValueError(f"Line {lineno}: cannot parse value: {raw!r}")


def load_toml_file(filepath: str) -> dict[str, Any]:
    """Load and parse a TOML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_toml(f.read())
