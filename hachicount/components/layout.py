"""Shared page layout helpers."""

import reflex as rx

from hachicount.navigation import hard_redirect
from hachicount.routes import AUTH_LOGOUT
from hachicount.settings import backend_base_url
from hachicount.states.auth import AuthState


def centered(*children: rx.Component) -> rx.Component:
    """A full-viewport shell that centers its children vertically and horizontally.

    Uses ``100dvh`` (dynamic viewport height) so it stays centered even with
    mobile browser chrome, and ``min_height`` so taller content can still scroll.
    """
    return rx.center(
        rx.color_mode.button(position="top-right"),
        *children,
        min_height="100dvh",
    )


def _topbar() -> rx.Component:
    """The app top bar: brand on the left, theme + logout on the right."""
    return rx.hstack(
        rx.hstack(
            rx.image(src="/logo.png", alt="Japan7 logo", height="2rem", width="auto"),
            rx.heading("Hachicount", size="5"),
            align="center",
            spacing="3",
        ),
        rx.spacer(),
        rx.hstack(
            rx.icon_button(
                rx.color_mode.icon(),
                on_click=rx.toggle_color_mode,
                variant="ghost",
                color_scheme="gray",
                aria_label="Toggle theme",
            ),
            rx.icon_button(
                rx.icon("log-out"),
                on_click=hard_redirect(backend_base_url() + AUTH_LOGOUT),
                variant="ghost",
                color_scheme="gray",
                aria_label="Log out",
            ),
            rx.avatar(
                fallback=AuthState.initials,
                variant="solid",
                radius="full",
                size="2",
            ),
            align="center",
            spacing="3",
        ),
        align="center",
        width="100%",
        padding="0.75rem 1rem",
        border_bottom="1px solid var(--gray-a5)",
    )


def authenticated_layout(*children: rx.Component) -> rx.Component:
    """The authenticated app layout: a top bar with the body centered below it."""

    return rx.cond(
        AuthState.is_authenticated,
        rx.vstack(
            _topbar(),
            rx.container(*children, width="100%", flex="1"),
            width="100%",
            min_height="100dvh",
        ),
        rx.center(
            rx.spinner(size="3"),
            min_height="100dvh",
        ),
    )
