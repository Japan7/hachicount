"""The protected home page."""

import reflex as rx

from hachicount.components.layout import authenticated_layout
from hachicount.states.user import CountView, UserState


def _count_row(count: CountView) -> rx.Component:
    """A single count in the list."""
    return rx.card(
        rx.text(count.name, weight="medium"),
        width="100%",
    )


def _empty_state() -> rx.Component:
    """Shown when the user does not take part in any count yet."""
    return rx.vstack(
        rx.icon("receipt-text", size=32, color="var(--gray-8)"),
        rx.text("You don't take part in any count yet.", color_scheme="gray"),
        align="center",
        spacing="2",
        padding_y="2rem",
        class_name="w-full",
    )


def index() -> rx.Component:
    """The protected home page: the user's counts.

    The page is loaded behind ``UserState.load_user`` (see ``hachicount.py``),
    which is the login wall and also populates ``UserState.counts``.
    """
    return authenticated_layout(
        rx.vstack(
            rx.heading("Your counts", size="8", align="center", class_name="w-full"),
            rx.cond(
                UserState.counts,
                rx.vstack(
                    rx.foreach(UserState.counts, _count_row),
                    spacing="2",
                ),
                _empty_state(),
            ),
            spacing="5",
        ),
    )
