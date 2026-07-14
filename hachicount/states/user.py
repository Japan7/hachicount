"""Reflex state holding the current user's local (database) account.

Sits on top of :class:`~hachicount.states.auth.AuthState`: it re-verifies the
session, then mirrors the matching database row's fields into state for the UI.
The account row is provisioned during login, so this state only reads it.
"""

import logging
from typing import Any

import reflex as rx

from hachicount.db.engine import transaction
from hachicount.db.errors import UserNotFoundError
from hachicount.db.models import User
from hachicount.db.users import get_user_by_email, update_user_name
from hachicount.routes import LOGIN_ROUTE
from hachicount.states.auth import AuthState

logger = logging.getLogger(__name__)


class UserState(rx.State):
    """The current user's local account, mirrored from the database."""

    # The user's own account fields, for display and editing. Populated by
    # ``load_user``; empty when unauthenticated. ``_id`` stays server-only.
    name: str = ""
    email: str = ""
    _id: str = ""

    # Working copy backing the profile form's (controlled) name input, so typing
    # does not mutate the displayed ``name`` until the change is saved.
    name_draft: str = ""

    @rx.var
    def initials(self) -> str:
        """Up to two uppercase initials for the current user's avatar fallback.

        Derived from the display ``name``, falling back to the ``email``
        local-part. Returns an empty string when unauthenticated (no name/email).
        """
        source = self.name or self.email.split("@")[0]
        letters = [part[0] for part in source.split() if part]
        return "".join(letters[:2]).upper()

    def _cache(self, user: User) -> None:
        """Mirror a database user's fields into state for the UI."""
        self._id = str(user.id)
        self.name = user.name
        self.email = user.email
        self.name_draft = user.name

    @rx.event
    async def load_user(self):
        """on_load guard + loader: verify the session and cache the account.

        Redirects to /login when the session is invalid, or when no local
        account matches it (which should not happen, since login provisions
        one — we re-authenticate rather than render a half-set-up page).
        """
        auth = await self.get_state(AuthState)
        claims = await auth.verify_session()
        if claims is None:
            return rx.redirect(LOGIN_ROUTE)

        with transaction() as session:
            user = get_user_by_email(session, claims["sub"])
            if user is None:
                logger.warning(
                    "No local account for the current session; re-authenticating"
                )
                return rx.redirect(LOGIN_ROUTE)
            self._cache(user)

    @rx.event
    def set_name_draft(self, value: str):
        """Track the profile form's (controlled) name input as the user types."""
        self.name_draft = value

    @rx.event
    async def save_name(self, form_data: dict[str, Any]):
        """Persist an edited display name submitted from the profile form."""
        auth = await self.get_state(AuthState)
        claims = await auth.verify_session()
        if claims is None:
            return rx.redirect(LOGIN_ROUTE)

        new_name = form_data.get("name", "").strip()
        if not new_name:
            return rx.toast.error("Name cannot be empty.")

        try:
            with transaction() as session:
                user = update_user_name(session, email=claims["sub"], name=new_name)
                self._cache(user)
        except UserNotFoundError:
            logger.warning(
                "Tried to rename a session with no local account; re-authenticating"
            )
            return rx.redirect(LOGIN_ROUTE)

        return rx.toast.success("Name updated.")
