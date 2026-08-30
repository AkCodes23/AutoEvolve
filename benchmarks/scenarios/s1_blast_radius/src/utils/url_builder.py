"""URL query builder utility with multi-parameter and sequence support."""
from urllib.parse import quote_plus


def build_query_url(base_url: str, params: dict, sort_keys: bool = True) -> str:
    """Construct a URL with query parameters.
    
    BUG: If a param value is a list/tuple, it stringifies it directly instead
    of creating repeated query parameters (e.g. key=val1&key=val2).
    """
    if not params:
        return base_url

    items = sorted(params.items()) if sort_keys else list(params.items())
    query_parts = []
    for key, value in items:
        # Broken behavior: str(value) turns ['active', 'pending'] into "['active',+'pending']"
        encoded_val = quote_plus(str(value))
        query_parts.append(f"{quote_plus(str(key))}={encoded_val}")

    delimiter = "&" if "?" in base_url else "?"
    return f"{base_url}{delimiter}{'&'.join(query_parts)}"
