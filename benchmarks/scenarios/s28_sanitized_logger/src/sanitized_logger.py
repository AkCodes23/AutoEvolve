"""Structured log sanitizer redacting sensitive tokens and credentials."""
from __future__ import annotations

import re
from typing import Any, Dict

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "api_key", "credit_card"}

BEARER_PATTERN = re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]+)", re.IGNORECASE)


def sanitize_log_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively mask secrets and sensitive credentials in dictionary log payloads."""
    sanitized: Dict[str, Any] = {}

    for k, v in record.items():
        if isinstance(v, dict):
            sanitized[k] = sanitize_log_record(v)
        elif isinstance(v, str):
            if k.lower() in SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                # Mask inline Bearer tokens
                sanitized[k] = BEARER_PATTERN.sub("Bearer [REDACTED]", v)
        else:
            sanitized[k] = v

    return sanitized
