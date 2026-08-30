import pytest
from benchmarks.scenarios.s1_blast_radius.src.services.auth import get_oauth_authorization_url


def test_get_oauth_authorization_url_multiple_scopes():
    url = get_oauth_authorization_url(
        client_id="app_xyz",
        scopes=["read:profile", "write:orders"],
        redirect_uri="https://app.example.com/oauth/callback"
    )
    expected = (
        "https://auth.example.com/oauth/v2/authorize?"
        "client_id=app_xyz&"
        "redirect_uri=https%3A%2F%2Fapp.example.com%2Foauth%2Fcallback&"
        "response_type=code&"
        "scope=read%3Aprofile&scope=write%3Aorders"
    )
    assert url == expected
