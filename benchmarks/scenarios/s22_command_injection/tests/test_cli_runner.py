"""Tests for subprocess command execution safety."""
import sys
import pytest
from benchmarks.scenarios.s22_command_injection.src.cli_runner import safe_run_command


def test_safe_execution():
    code, out, err = safe_run_command([sys.executable, "-c", "print('hello_safe')"])
    assert code == 0
    assert "hello_safe" in out


def test_command_injection_attempt_is_treated_as_literal():
    # Attempting to inject shell chaining
    malicious_arg = "foo; echo pwned"
    code, out, err = safe_run_command([sys.executable, "-c", "import sys; print(sys.argv[1])", malicious_arg])
    assert code == 0
    assert "foo; echo pwned" in out
    assert "pwned" not in err


def test_invalid_arguments_raise():
    with pytest.raises(ValueError):
        safe_run_command([])
