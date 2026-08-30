"""Payment gateway client with proper error categorization."""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any


class ClientError(Exception):
    """Raised for client-side errors (invalid input, bad request)."""
    pass


class DependencyError(Exception):
    """Raised for external dependency failures (network, upstream API)."""
    pass


class ServerError(Exception):
    """Raised for internal server errors."""
    pass


class PaymentGateway:
    """Payment processing client with categorized error handling."""

    def __init__(self, api_url: str, timeout: int = 10):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def charge(self, amount: float, currency: str, card_token: str) -> dict[str, Any]:
        """Process a payment charge.

        Raises:
            ClientError: For invalid input (negative amount, empty token).
            DependencyError: For network/upstream failures.
            ServerError: For unexpected internal errors.
        """
        if amount <= 0:
            raise ClientError(f"Invalid amount: {amount}. Must be positive.")
        if not card_token or not card_token.strip():
            raise ClientError("Card token must not be empty.")
        if currency not in ("USD", "EUR", "GBP", "INR", "JPY"):
            raise ClientError(f"Unsupported currency: {currency!r}")

        url = f"{self.api_url}/charge"
        data = f'{{"amount":{amount},"currency":"{currency}","token":"{card_token}"}}'

        try:
            req = urllib.request.Request(
                url,
                data=data.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return {"status": "success", "code": resp.status}
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise ClientError(f"API rejected request: HTTP {exc.code}") from exc
            raise DependencyError(f"Upstream API error: HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DependencyError(f"Network failure: {exc}") from exc
        except Exception as exc:
            raise ServerError(f"Unexpected error during charge: {exc}") from exc

    def refund(self, transaction_id: str, amount: float) -> dict[str, Any]:
        """Process a refund.

        Raises:
            ClientError: For invalid input.
            DependencyError: For network/upstream failures.
            ServerError: For unexpected internal errors.
        """
        if not transaction_id:
            raise ClientError("Transaction ID must not be empty.")
        if amount <= 0:
            raise ClientError(f"Refund amount must be positive, got {amount}.")

        url = f"{self.api_url}/refund"
        try:
            req = urllib.request.Request(
                url,
                data=f'{{"txn_id":"{transaction_id}","amount":{amount}}}'.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return {"status": "refunded", "code": resp.status}
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise ClientError(f"Refund rejected: HTTP {exc.code}") from exc
            raise DependencyError(f"Upstream error: HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DependencyError(f"Network failure: {exc}") from exc
        except Exception as exc:
            raise ServerError(f"Unexpected error during refund: {exc}") from exc
