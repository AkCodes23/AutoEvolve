"""User repository supporting dual-write transition from full_name to (first_name, last_name)."""
from __future__ import annotations

from typing import Any, Dict, Optional


class UserRepository:
    """In-memory database repository with zero-downtime dual-write schema migration."""

    def __init__(self):
        self._records: Dict[str, Dict[str, Any]] = {}

    def save_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save user record supporting both legacy full_name and new first/last name fields."""
        if not user_id:
            raise ValueError("user_id is required")

        # Derive missing fields
        if full_name and not (first_name or last_name):
            parts = full_name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
        elif first_name and not full_name:
            full_name = f"{first_name} {last_name or ''}".strip()

        record = {
            "id": user_id,
            "first_name": first_name or "",
            "last_name": last_name or "",
            "full_name": full_name or "",
        }
        self._records[user_id] = record
        return record

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record."""
        return self._records.get(user_id)
