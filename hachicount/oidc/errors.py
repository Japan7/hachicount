"""Exceptions raised by the OIDC client.

These let the rest of the app depend on our own domain types instead of on the
exception classes of whatever libraries the client uses internally (Authlib and
the HTTP transport under it). ``client.py`` is the single place that translates
those library exceptions into the ones below.
"""


class OIDCError(RuntimeError):
    """Base class for OIDC login-wall failures surfaced by the client."""


class OIDCConfigError(OIDCError):
    """OIDC configuration is missing, or the provider metadata is unusable.

    Raised when the required ``OIDC_*`` environment variables are absent, or when
    the provider's discovery document omits an endpoint we need.
    """


class OIDCUnavailableError(OIDCError):
    """The provider could not be reached — a transport-level failure.

    Kept distinct from an invalid token on purpose: a caller may keep an
    already-verified session alive across a brief provider outage rather than
    signing the user out.
    """
