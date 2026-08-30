import pytest
from benchmarks.scenarios.s1_blast_radius.src.services.analytics import build_telemetry_event_url


def test_build_telemetry_event_url_with_tags():
    url = build_telemetry_event_url("button_click", ["ui", "checkout", "v2"], "sess_789")
    expected = (
        "https://telemetry.example.com/v1/collect?"
        "event=button_click&"
        "sid=sess_789&"
        "tag=ui&tag=checkout&tag=v2"
    )
    assert url == expected
