"""Application route paths, shared across pages, state, and backend routes."""

# Reflex frontend pages.
HOME_ROUTE = "/"
LOGIN_ROUTE = "/auth/login"
PROFILE_ROUTE = "/profile"

# Backend HTTP routes (served by the ASGI app, not Reflex pages) that drive the
# OIDC flow and set/clear the HttpOnly session cookie. `AUTH_CALLBACK` is the
# redirect URI to register with the provider (on the backend base URL).
AUTH_LOGIN = "/api/auth/login"
AUTH_CALLBACK = "/api/auth/callback"
AUTH_LOGOUT = "/api/auth/logout"
