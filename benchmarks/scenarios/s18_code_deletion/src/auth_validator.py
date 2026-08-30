"""Minimal direct token validation without dead abstraction layers."""
from __future__ import annotations

import hmac
import hashlib


def validate_bearer_token(auth_header: str, secret_key: str) -> bool:
    """Validate Bearer token against secret HMAC signature in 5 direct lines."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:].strip()
    expected = hmac.new(secret_key.encode("utf-8"), b"auth_payload", hashlib.sha256).hexdigest()
    return hmac.compare_digest(token, expected)
