"""Backend HTTP routes for the OIDC login wall.

Unlike Reflex state events (which run over the websocket, where cookies can only
be set from JavaScript), these are real HTTP requests, so they set the session
cookie via ``Set-Cookie`` with ``HttpOnly`` + ``Secure`` — keeping the id_token
out of reach of JavaScript/XSS. They reuse the framework-agnostic client in
``hachicount.oidc`` and are mounted on the app via ``api_transformer``.
"""

import json
import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from hachicount.oidc import OIDCError, get_oidc_client
from hachicount.routes import (
    AUTH_CALLBACK,
    AUTH_LOGIN,
    AUTH_LOGOUT,
    HOME_ROUTE,
    LOGIN_ROUTE,
)
from hachicount.settings import (
    AUTH_TX_COOKIE,
    ID_TOKEN_COOKIE,
    app_base_url,
    backend_base_url,
    cookie_secure,
)

logger = logging.getLogger(__name__)

# How long a user has to complete the login round-trip before the transaction
# cookie expires.
_TX_MAX_AGE = 600  # seconds

# HTTP 303 turns the provider's redirect into a plain GET of the next page.
_SEE_OTHER = 303


def _redirect_uri() -> str:
    """The callback URL to register with the provider (on the backend base)."""
    return backend_base_url() + AUTH_CALLBACK


def _set_tx_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        AUTH_TX_COOKIE,
        value,
        max_age=_TX_MAX_AGE,
        httponly=True,
        secure=cookie_secure(),
        samesite="lax",
        path=AUTH_CALLBACK,
    )


def _clear_tx_cookie(response: Response) -> None:
    response.delete_cookie(AUTH_TX_COOKIE, path=AUTH_CALLBACK)


async def login(request: Request) -> Response:
    """Start the OIDC flow: store the PKCE/CSRF transaction, redirect to the IdP."""
    try:
        auth_request = await get_oidc_client().create_authorization_request(
            _redirect_uri()
        )
    except OIDCError:
        logger.warning("Cannot start login", exc_info=True)
        return RedirectResponse(app_base_url() + LOGIN_ROUTE, status_code=_SEE_OTHER)

    response = RedirectResponse(auth_request.url, status_code=_SEE_OTHER)
    _set_tx_cookie(
        response,
        json.dumps(
            {
                "state": auth_request.state,
                "nonce": auth_request.nonce,
                "verifier": auth_request.code_verifier,
            }
        ),
    )
    return response


async def callback(request: Request) -> Response:
    """Handle the IdP redirect: verify, set the id_token cookie, land in the app."""

    def fail() -> Response:
        response = RedirectResponse(
            app_base_url() + LOGIN_ROUTE, status_code=_SEE_OTHER
        )
        _clear_tx_cookie(response)
        return response

    params = request.query_params
    tx_raw = request.cookies.get(AUTH_TX_COOKIE)
    if params.get("error") or not tx_raw:
        logger.warning(
            "OIDC callback error or missing transaction: %s", params.get("error")
        )
        return fail()
    try:
        tx = json.loads(tx_raw)
    except ValueError:
        logger.warning("OIDC callback transaction cookie was malformed")
        return fail()

    # CSRF: a login must be pending (non-empty stored state) and match exactly.
    code = params.get("code")
    if not code or not tx.get("state") or params.get("state") != tx["state"]:
        logger.warning("OIDC callback failed the state/CSRF check")
        return fail()

    try:
        client = get_oidc_client()
        id_token = await client.exchange_code(code, tx["verifier"], _redirect_uri())
        claims = await client.verify_id_token(id_token, nonce=tx.get("nonce", ""))
    except OIDCError:
        logger.warning("Authorization code exchange failed", exc_info=True)
        return fail()
    if claims is None:
        logger.warning("ID token verification failed after code exchange")
        return fail()

    response = RedirectResponse(app_base_url() + HOME_ROUTE, status_code=_SEE_OTHER)
    response.set_cookie(
        ID_TOKEN_COOKIE,
        id_token,
        httponly=True,
        secure=cookie_secure(),
        samesite="lax",
        path="/",
    )
    _clear_tx_cookie(response)
    return response


async def logout(request: Request) -> Response:
    """Clear the local session cookie and return to the login page.

    Local logout only: we do not hit the provider's end_session_endpoint (it
    rejects RP-initiated logout without a registered post_logout_redirect_uri),
    so the user stays signed in at the provider.
    """
    response = RedirectResponse(app_base_url() + LOGIN_ROUTE, status_code=_SEE_OTHER)
    response.delete_cookie(ID_TOKEN_COOKIE, path="/")
    return response


def build_auth_api() -> Starlette:
    """Return the Starlette app exposing the auth routes, for ``api_transformer``."""
    return Starlette(
        routes=[
            Route(AUTH_LOGIN, login, methods=["GET"]),
            Route(AUTH_CALLBACK, callback, methods=["GET"]),
            Route(AUTH_LOGOUT, logout, methods=["GET"]),
        ]
    )
