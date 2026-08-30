"""Authentication and authorization service client."""
from ..utils.url_builder import build_query_url


def get_oauth_authorization_url(client_id: str, scopes: list[str], redirect_uri: str) -> str:
    """Generate OAuth2 authorization endpoint URL."""
    params = {
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "response_type": "code",
    }
    return build_query_url("https://auth.example.com/oauth/v2/authorize", params, sort_keys=True)
