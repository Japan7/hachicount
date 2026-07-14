"""The protected home page."""

import reflex as rx

from hachicount.components.layout import authenticated_layout
from hachicount.states.count import CountState, CountView


def _count_row(count: CountView) -> rx.Component:
    """A single count in the list."""
    return rx.card(
        rx.text(count.name, weight="medium"),
        class_name="w-full",
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


def _heading() -> rx.Component:
    """The page title with the "new count" action aligned to its right."""
    return rx.hstack(
        rx.heading("Your counts", size="8"),
        _new_count_dialog(),
        align="end",
        justify="between",
        class_name="w-full",
    )


def _new_count_dialog() -> rx.Component:
    """A button opening a dialog to name and create a new count."""
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button("New count"),
        ),
        rx.dialog.content(
            rx.dialog.title("New count"),
            rx.dialog.description(
                "Give your count a name",
                margin_bottom="0.5rem",
            ),
            rx.form(
                rx.vstack(
                    rx.input(
                        name="name",
                        value=CountState.name_draft,
                        on_change=CountState.set_name_draft,
                        placeholder="e.g. Jeanjean Camp™",
                        required=True,
                        auto_focus=True,
                        class_name="w-full",
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button(
                                "Cancel",
                                type="button",
                                variant="soft",
                                color_scheme="gray",
                            ),
                        ),
                        rx.button("Create", type="submit"),
                        justify="end",
                        class_name="w-full",
                    ),
                    spacing="4",
                    class_name="w-full",
                ),
                on_submit=CountState.create_count,
            ),
            max_width="26rem",
        ),
        open=CountState.create_open,
        on_open_change=CountState.set_create_open,
    )


def index() -> rx.Component:
    """The protected home page: the user's counts.

    Loaded behind ``UserState.load_user`` + ``CountState.load_counts`` (see
    ``hachicount.py``); the former is the login wall and populates the topbar,
    the latter fills the counts list below.
    """
    return authenticated_layout(
        rx.vstack(
            _heading(),
            rx.cond(
                CountState.counts,
                rx.vstack(
                    rx.foreach(CountState.counts, _count_row),
                    spacing="2",
                    class_name="w-full",
                ),
                _empty_state(),
            ),
            spacing="5",
        ),
    )
