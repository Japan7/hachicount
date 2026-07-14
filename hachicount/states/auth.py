"""Reflex state for the OIDC login wall (read-only session guard).

The OIDC flow itself lives in the backend routes (``hachicount.auth_api``), which
set the ``HttpOnly`` id_token cookie. This state never writes cookies: it reads
the incoming id_token from the request headers and verifies it, gating pages and
event handlers. Because the cookie is ``HttpOnly`` it is invisible to
JavaScript, and because it is a provider-signed JWT re-verified server-side
(signature, issuer, audience, expiry) on every check, a tampered or expired
cookie is always rejected.
"""

import logging
from http.cookies import SimpleCookie
from typing import Any

import reflex as rx

from hachicount.oidc import OIDCUnavailableError, get_oidc_client
from hachicount.routes import HOME_ROUTE, LOGIN_ROUTE
from hachicount.settings import ID_TOKEN_COOKIE

logger = logging.getLogger(__name__)


class AuthState(rx.State):
    """Read-only session state: verifies the incoming id_token cookie."""

    # Verified claims for the current user (server-only; never trusted from the
    # client). Refreshed from the id_token cookie by ``verify_session``.
    _claims: dict[str, Any] = {}

    @rx.var
    def is_authenticated(self) -> bool:
        """Whether the current user was verified on the last session check."""
        return bool(self._claims)

    def _id_token(self) -> str:
        """Read the id_token from the incoming request's Cookie header."""
        raw = self.router.headers.cookie
        if not raw:
            return ""
        jar = SimpleCookie()
        try:
            jar.load(raw)
        except Exception:
            return ""
        morsel = jar.get(ID_TOKEN_COOKIE)
        return morsel.value if morsel else ""

    async def verify_session(self) -> dict[str, Any] | None:
        """Re-verify the id_token cookie and refresh the cached claims.

        The single source of truth for "is this request authenticated?". Call it
        at the start of any event handler that reads or mutates protected data:
        it re-checks the signature and expiry *every* time, so a page opened
        while logged in cannot keep acting once the token expires. Returns the
        verified claims, or ``None`` when the user is not authenticated.

        A genuinely invalid/expired token drops the cached claims. A transient
        provider/network failure does not: we fall back to the claims already
        verified this session, so a brief provider outage does not knock every
        user out mid-session. (The HttpOnly cookie is cleared by /auth/logout,
        not from here.)
        """
        try:
            claims = await get_oidc_client().verify_id_token(self._id_token())
        except OIDCUnavailableError as exc:
            logger.warning(
                "Could not verify session (provider unavailable); keeping the "
                "existing session: %s",
                exc,
                exc_info=True,
            )
            return self._claims or None
        if claims is None:
            self._claims = {}
            return None
        self._claims = claims
        return claims

    @rx.event
    async def require_login(self):
        """on_load guard: allow authenticated users, else redirect to /login."""
        if await self.verify_session() is None:
            return rx.redirect(LOGIN_ROUTE)

    @rx.event
    async def redirect_if_authenticated(self):
        """on_load guard for /login: skip the page when already signed in."""
        if await self.verify_session() is not None:
            return rx.redirect(HOME_ROUTE)
