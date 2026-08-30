"""Telemetry and analytics event publisher."""
from ..utils.url_builder import build_query_url


def build_telemetry_event_url(event_name: str, tags: list[str], session_id: str) -> str:
    """Construct event tracking pixel beacon URL."""
    params = {
        "event": event_name,
        "tag": tags,
        "sid": session_id,
    }
    return build_query_url("https://telemetry.example.com/v1/collect", params, sort_keys=True)
