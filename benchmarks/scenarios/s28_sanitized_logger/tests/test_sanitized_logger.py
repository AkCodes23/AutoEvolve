"""Tests for sensitive log payload redaction."""
from benchmarks.scenarios.s28_sanitized_logger.src.sanitized_logger import sanitize_log_record


def test_sensitive_keys_redacted():
    payload = {
        "user_id": "u123",
        "password": "SuperSecretPassword123!",
        "api_key": "sk-proj-99999999",
        "nested": {
            "token": "ghp_1234567890abcdef",
        },
    }
    sanitized = sanitize_log_record(payload)
    assert sanitized["user_id"] == "u123"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"


def test_bearer_token_string_redacted():
    payload = {
        "message": "User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    }
    sanitized = sanitize_log_record(payload)
    assert "Bearer [REDACTED]" in sanitized["message"]
    assert "eyJhbGci" not in sanitized["message"]
