"""Auth cookie names and URLs, derived from the Reflex configuration.

The base URLs come straight from Reflex's own config so there is nothing extra
to configure: ``api_url`` is the backend (where the auth routes and the OIDC
``redirect_uri`` live) and ``deploy_url`` is the public frontend (where users
land after login/logout). In local dev these are http://localhost:8000 and
http://localhost:3000; in production set them (or REFLEX_API_URL /
REFLEX_DEPLOY_URL) to your real URLs — a single-port deployment uses one origin
for both.
"""

from reflex.config import get_config

# The verified id_token (a signed JWT). Set HttpOnly + Secure by the backend
# auth routes, so it is never readable from JavaScript (XSS-safe).
ID_TOKEN_COOKIE = "hc_id_token"

# Short-lived cookie holding the in-flight login transaction (PKCE verifier +
# CSRF state + nonce) between /auth/login and /auth/callback.
AUTH_TX_COOKIE = "hc_auth_tx"


def backend_base_url() -> str:
    """Base URL of the backend, where the auth routes and redirect_uri live."""
    return get_config().api_url.rstrip("/")


def app_base_url() -> str:
    """Public URL of the frontend, where users land after login/logout."""
    return (get_config().deploy_url or "").rstrip("/")


def cookie_secure() -> bool:
    """Whether auth cookies are marked Secure (backend served over https)."""
    return backend_base_url().startswith("https://")
