"""OIDC provider configuration, loaded and validated once from the environment."""

import os
from dataclasses import dataclass
from functools import cache

from hachicount.oidc.errors import OIDCConfigError

_ENV_VARS = ("OIDC_ISSUER_URI", "OIDC_CLIENT_ID", "OIDC_CLIENT_SECRET")


@dataclass(frozen=True)
class OIDCSettings:
    """Static configuration for the OIDC provider."""

    issuer: str
    client_id: str
    client_secret: str

    @property
    def discovery_url(self) -> str:
        """The OpenID Connect discovery document URL for this issuer."""
        return f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"


@cache
def get_settings() -> OIDCSettings:
    """Load and validate the OIDC settings once, failing fast if any are missing.

    On success the result is cached for the process. A failure is *not* cached,
    so a later call (e.g. after fixing ``.env`` and reloading) retries cleanly.
    """
    missing = [name for name in _ENV_VARS if not os.environ.get(name)]
    if missing:
        raise OIDCConfigError(
            "Missing OIDC configuration: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your provider credentials."
        )
    return OIDCSettings(
        issuer=os.environ["OIDC_ISSUER_URI"],
        client_id=os.environ["OIDC_CLIENT_ID"],
        client_secret=os.environ["OIDC_CLIENT_SECRET"],
    )
