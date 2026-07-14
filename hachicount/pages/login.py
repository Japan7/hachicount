"""Public login page (form only; the OIDC flow runs on the backend)."""

import reflex as rx

from hachicount.components.layout import centered
from hachicount.navigation import hard_redirect
from hachicount.routes import AUTH_LOGIN
from hachicount.settings import backend_base_url


def login() -> rx.Component:
    """Public login page: the single "sign in" entry point to the app.

    "Sign in" navigates to the backend ``/auth/login`` route, which starts the
    OIDC flow. It is an external navigation because that route may live on a
    different origin than the frontend during development.
    """
    return centered(
        rx.card(
            rx.vstack(
                rx.image(
                    src="/logo.png",
                    alt="Japan7 logo",
                    width="8rem",
                    height="auto",
                ),
                rx.heading("Hachicount"),
                rx.button(
                    "Sign in using NanaOIDC",
                    on_click=hard_redirect(backend_base_url() + AUTH_LOGIN),
                    size="4",
                ),
                align="center",
                spacing="5",
                class_name="p-10",
            ),
        ),
    )
