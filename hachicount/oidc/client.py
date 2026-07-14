"""A small async OpenID Connect client: discovery, verification, code exchange.

Framework-agnostic — it knows nothing about Reflex. The Reflex glue that stores
the session and drives the login events lives in ``hachicount.states.auth``.

This is a thin wrapper over Authlib's OIDC client (``StarletteOAuth2App``): that
object owns the provider discovery document + JWKS caching (on this one shared
instance) and the audited id_token verification, so we implement none of that by
hand. ``OAuth``/``StarletteIntegration`` here is only Authlib's async HTTP glue —
it does not tie us to a web framework, and we deliberately skip its session-backed
redirect helpers; our HttpOnly-cookie flow lives in ``hachicount.auth_api``.
"""

import logging
from dataclasses import dataclass
from functools import cache
from typing import Any

import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from authlib.oidc.core import CodeIDToken

from hachicount.oidc.errors import (
    OIDCConfigError,
    OIDCError,
    OIDCUnavailableError,
)
from hachicount.oidc.settings import OIDCSettings, get_settings

logger = logging.getLogger(__name__)

# Requested scopes. `openid` is required; `email`/`profile` give the display
# claims we show on the home page.
SCOPES = "openid"


@dataclass(frozen=True)
class AuthorizationRequest:
    """Everything needed to start, then later complete, an auth-code+PKCE flow."""

    url: str  # where to send the user's browser
    state: str  # CSRF token echoed back on the callback
    nonce: str  # replay-protection nonce bound into the id_token
    code_verifier: str  # PKCE verifier presented at token exchange


class OIDCClient:
    """Talks to one OIDC provider via Authlib's OIDC client.

    Authlib caches the discovery document and JWKS on the underlying app, so a
    single shared ``OIDCClient`` (see ``get_oidc_client``) fetches each once and
    reuses them across requests, refreshing the JWKS itself on key rotation.
    """

    def __init__(self, settings: OIDCSettings) -> None:
        self._settings = settings
        # `client_secret_basic` (Authlib's default once a secret is set) is what
        # the provider expects; `code_challenge_method` turns on PKCE. Authlib
        # also generates the state/nonce/verifier and validates the id_token.
        self._app = OAuth().register(
            name="oidc",
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            server_metadata_url=settings.discovery_url,
            client_kwargs={
                "scope": SCOPES,
                "code_challenge_method": "S256",
            },
        )

    async def create_authorization_request(
        self, redirect_uri: str
    ) -> AuthorizationRequest:
        """Build the authorization URL and the PKCE/CSRF material to store.

        Authlib generates the ``state``/``nonce``/``code_verifier`` and folds the
        PKCE challenge into the URL. Raises ``OIDCUnavailableError`` if the
        discovery document can't be fetched, or ``OIDCConfigError`` if it is too
        broken to yield an authorization endpoint.
        """
        try:
            rv = await self._app.create_authorization_url(redirect_uri)
        except httpx.HTTPError as exc:
            raise OIDCUnavailableError("Could not reach the OIDC provider.") from exc
        except RuntimeError as exc:  # e.g. no authorization_endpoint in metadata
            raise OIDCConfigError(str(exc)) from exc
        return AuthorizationRequest(
            url=rv["url"],
            state=rv["state"],
            nonce=rv["nonce"],
            code_verifier=rv["code_verifier"],
        )

    async def exchange_code(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> str:
        """Exchange an authorization code for tokens; return the raw id_token.

        Uses the confidential-client credentials plus the PKCE ``code_verifier``.
        Raises ``OIDCUnavailableError`` on a transport failure, or ``OIDCError``
        when the provider rejects the exchange or returns no id_token.
        """
        try:
            token = await self._app.fetch_access_token(
                redirect_uri=redirect_uri,
                code=code,
                code_verifier=code_verifier,
            )
        except httpx.HTTPError as exc:
            raise OIDCUnavailableError("Could not reach the OIDC provider.") from exc
        except OAuthError as exc:
            raise OIDCError(f"Provider rejected the code exchange: {exc}") from exc
        try:
            return token["id_token"]
        except KeyError as exc:
            raise OIDCError("Token response did not include an id_token.") from exc

    async def verify_id_token(
        self, id_token: str, *, nonce: str = ""
    ) -> dict[str, Any] | None:
        """Verify an id_token and return its claims, or ``None`` if invalid.

        Delegates to Authlib, which checks the signature against the provider
        JWKS (refreshing once on key rotation) and validates issuer, audience and
        expiry; when ``nonce`` is given (right after login) it must match the
        token's ``nonce`` claim. ``CodeIDToken`` is forced so re-verifying a
        stored token (no nonce, no access_token) does not trip the implicit-flow
        rule that would otherwise require a nonce.

        Fetching the provider metadata/JWKS can raise ``OIDCUnavailableError``;
        that propagates so the caller can tell "provider unavailable" apart from
        an invalid token. ``None`` is returned *only* when the token is genuinely
        invalid, never for a transient provider/network failure.
        """
        if not id_token:
            return None
        try:
            claims = await self._app.parse_id_token(
                {"id_token": id_token}, nonce or None, claims_cls=CodeIDToken
            )
        except httpx.HTTPError as exc:
            # Provider/network failure while fetching metadata/JWKS — not an
            # invalid token, so surface it as such rather than as "logged out".
            raise OIDCUnavailableError(
                "Could not reach the OIDC provider to verify the token."
            ) from exc
        except Exception as exc:  # bad signature, claims, or format → invalid
            logger.warning("ID token verification failed: %s", exc)
            return None
        return dict(claims)


@cache
def get_oidc_client() -> OIDCClient:
    """Return the process-wide OIDC client, validating settings on first use."""
    return OIDCClient(get_settings())
