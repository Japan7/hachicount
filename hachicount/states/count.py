"""Reflex state for the counts the current user takes part in.

Like :class:`~hachicount.states.user.UserState`, it sits on top of
:class:`~hachicount.states.auth.AuthState`: every entry point re-verifies the
session before touching the database, so a stale page cannot read or mutate
counts once its token has expired.
"""

import dataclasses
import logging
from typing import Any

import reflex as rx

from hachicount.db.counts import create_count, get_counts_for_user
from hachicount.db.engine import transaction
from hachicount.db.models import Count
from hachicount.db.participants import add_participant
from hachicount.db.users import get_user_by_email
from hachicount.routes import LOGIN_ROUTE
from hachicount.states.auth import AuthState

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CountView:
    """A count as shown in the UI (ids as strings, safe to send to the client)."""

    id: str
    name: str


class CountState(rx.State):
    """The current user's counts, plus creating new ones."""

    # The counts the user takes part in, refreshed by ``load_counts``.
    counts: list[CountView] = []

    # Controlled state for the "new count" dialog and its (controlled) input.
    create_open: bool = False
    name_draft: str = ""

    async def _verified_email(self) -> str | None:
        """The current session's account email, or ``None`` if unauthenticated."""
        auth = await self.get_state(AuthState)
        claims = await auth.verify_session()
        return claims["sub"] if claims else None

    @staticmethod
    def _view(counts: list[Count]) -> list[CountView]:
        return [CountView(id=str(count.id), name=count.name) for count in counts]

    @rx.event
    async def load_counts(self):
        """on_load: verify the session and refresh the user's counts."""
        email = await self._verified_email()
        if email is None:
            return rx.redirect(LOGIN_ROUTE)
        with transaction() as session:
            user = get_user_by_email(session, email)
            if user is None:
                logger.warning(
                    "No local account for the current session; re-authenticating"
                )
                return rx.redirect(LOGIN_ROUTE)
            self.counts = self._view(get_counts_for_user(session, user.id))

    @rx.event
    def set_create_open(self, is_open: bool):
        """Open/close the dialog, clearing the input each time it opens."""
        self.create_open = is_open
        if is_open:
            self.name_draft = ""

    @rx.event
    def set_name_draft(self, value: str):
        """Track the dialog's (controlled) name input as the user types."""
        self.name_draft = value

    @rx.event
    async def create_count(self, form_data: dict[str, Any]):
        """Create a count and enrol the current user as its first participant."""
        email = await self._verified_email()
        if email is None:
            return rx.redirect(LOGIN_ROUTE)

        name = form_data.get("name", "").strip()
        if not name:
            return rx.toast.error("Count name cannot be empty.")

        with transaction() as session:
            user = get_user_by_email(session, email)
            if user is None:
                return rx.redirect(LOGIN_ROUTE)
            count = create_count(session, name=name)
            add_participant(session, count_id=count.id, user=user, name=user.name)
            self.counts = self._view(get_counts_for_user(session, user.id))

        self.create_open = False
        return rx.toast.success(f"Count “{name}” created.")
