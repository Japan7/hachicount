"""The protected home page."""

import reflex as rx

from hachicount.components.layout import authenticated_layout


def index() -> rx.Component:
    """The protected home page.

    ``on_load=AuthState.require_login`` is the login wall: an unauthenticated
    visitor is redirected to /login before any content is shown.
    """
    return authenticated_layout(
        rx.vstack(
            rx.heading("Hello World!", size="8"),
            align="center",
        ),
    )
