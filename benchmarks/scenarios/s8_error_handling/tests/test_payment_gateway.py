"""Tests for payment gateway error categorization."""
from __future__ import annotations

import ast
import os

import pytest

from benchmarks.scenarios.s8_error_handling.src.payment_gateway import (
    ClientError,
    DependencyError,
    PaymentGateway,
    ServerError,
)


class TestClientErrors:
    def test_negative_amount_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError, match="[Ii]nvalid amount"):
            gw.charge(-50.0, "USD", "tok_valid")

    def test_zero_amount_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError):
            gw.charge(0, "USD", "tok_valid")

    def test_empty_token_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError, match="[Tt]oken"):
            gw.charge(10.0, "USD", "")

    def test_unsupported_currency_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError, match="[Uu]nsupported"):
            gw.charge(10.0, "ZZZ", "tok_valid")

    def test_empty_transaction_id_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError):
            gw.refund("", 10.0)

    def test_negative_refund_raises_client_error(self):
        gw = PaymentGateway("http://fake.test", timeout=1)
        with pytest.raises(ClientError):
            gw.refund("txn_123", -5.0)


class TestDependencyErrors:
    def test_unreachable_host_raises_dependency_error(self):
        gw = PaymentGateway("http://192.0.2.1:1", timeout=1)
        with pytest.raises(DependencyError, match="[Nn]etwork|[Tt]imeout|[Cc]onnect"):
            gw.charge(10.0, "USD", "tok_valid")


class TestTimeoutPresent:
    def test_timeout_attribute_is_set(self):
        gw = PaymentGateway("http://fake.test", timeout=5)
        assert gw.timeout == 5

    def test_default_timeout_is_reasonable(self):
        gw = PaymentGateway("http://fake.test")
        assert 1 <= gw.timeout <= 30


class TestSourceCodeQuality:
    """AST-level analysis of the source code."""

    @staticmethod
    def _get_source_tree():
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "payment_gateway.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            return ast.parse(f.read())

    def test_no_bare_except(self):
        tree = self._get_source_tree()
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    pytest.fail(
                        f"Bare 'except:' found at line {node.lineno}. "
                        "Must use typed exception handlers."
                    )

    def test_has_typed_exception_classes(self):
        tree = self._get_source_tree()
        class_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "Exception":
                        class_names.add(node.name)
        assert len(class_names) >= 2, (
            f"Expected at least 2 custom exception classes, found: {class_names}"
        )

    def test_timeout_used_in_urlopen(self):
        src_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "payment_gateway.py"
        )
        with open(src_path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "timeout" in source, "Expected timeout parameter in network calls"
