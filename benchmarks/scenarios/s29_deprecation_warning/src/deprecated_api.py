"""Graceful API deprecation with structured warnings and delegation."""
from __future__ import annotations

import warnings
from typing import List


def fetch_users_v2(filter_active: bool = True) -> List[str]:
    """Modern user fetcher returning list of usernames."""
    return ["alice", "bob"] if filter_active else ["alice", "bob", "charlie"]


def get_all_users() -> List[str]:
    """Legacy user fetcher. Deprecated in favor of fetch_users_v2()."""
    warnings.warn(
        "get_all_users() is deprecated and will be removed in v3.0; use fetch_users_v2() instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return fetch_users_v2(filter_active=False)
