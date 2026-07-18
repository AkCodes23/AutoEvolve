"""A list endpoint. Code under test. See README.md.

TASK: add a `page` parameter. With no page, behave exactly as today (return all items).
With page=N (1-based), return that page of `per_page` items. Reject an invalid page.
"""

_ITEMS = list(range(1, 26))  # 25 items: 1..25


def list_items(page=None, per_page=10):
    # Starter: ignores pagination and always returns everything.
    return list(_ITEMS)
