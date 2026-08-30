"""Tests for minimal token validator."""
import hashlib
import hmac
import inspect
from benchmarks.scenarios.s18_code_deletion.src.auth_validator import validate_bearer_token


def test_valid_token():
    secret = "my-secret-key"
    token = hmac.new(secret.encode("utf-8"), b"auth_payload", hashlib.sha256).hexdigest()
    assert validate_bearer_token(f"Bearer {token}", secret) is True


def test_invalid_token():
    assert validate_bearer_token("Bearer wrong-token", "my-secret-key") is False
    assert validate_bearer_token("Basic 123", "my-secret-key") is False
    assert validate_bearer_token("", "my-secret-key") is False


def test_ast_brevity_no_excess_classes():
    """Verify that no speculative classes or factories are present."""
    from benchmarks.scenarios.s18_code_deletion.src import auth_validator
    source = inspect.getsource(auth_validator)
    # Must not contain class definitions or factory boilerplate
    assert "class " not in source
    assert "Abstract" not in source
