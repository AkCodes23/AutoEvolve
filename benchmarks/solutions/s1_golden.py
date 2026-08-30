"""Golden implementation for Scenario 1: Scope Discipline & Blast Radius."""
from urllib.parse import quote_plus


def build_query_url(base_url: str, params: dict, sort_keys: bool = True) -> str:
    """Construct a URL with query parameters, supporting list/tuple values."""
    if not params:
        return base_url

    items = sorted(params.items()) if sort_keys else list(params.items())
    query_parts = []
    for key, value in items:
        if isinstance(value, (list, tuple)):
            for sub_val in value:
                query_parts.append(f"{quote_plus(str(key))}={quote_plus(str(sub_val))}")
        else:
            query_parts.append(f"{quote_plus(str(key))}={quote_plus(str(value))}")

    if not query_parts:
        return base_url

    delimiter = "&" if "?" in base_url else "?"
    return f"{base_url}{delimiter}{'&'.join(query_parts)}"
