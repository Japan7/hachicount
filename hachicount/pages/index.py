"""The protected home page."""

import reflex as rx

from hachicount.components.layout import authenticated_layout
from hachicount.states.count import CountState, CountView


def _count_row(count: CountView) -> rx.Component:
    """A single count in the list, with a button to leave it."""
    return rx.card(
        rx.hstack(
            rx.text(count.name, weight="medium"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("log-out", size=18),
                on_click=CountState.ask_leave(count.id, count.name),
                variant="ghost",
                color_scheme="red",
                aria_label="Leave count",
                cursor="pointer",
            ),
            align="center",
            class_name="w-full",
        ),
        class_name="w-full",
    )


def _leave_dialog() -> rx.Component:
    """The shared confirmation for leaving a count (opened via ``ask_leave``).

    A single controlled dialog reused by every row: the row's button records the
    target and opens it, and the warning changes when leaving would delete the
    count.
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Leave ", CountState.leave_name),
            rx.dialog.description(
                rx.cond(
                    CountState.leave_is_last,
                    "You're the last participant of this count. "
                    "If you leave now, it will be permanently deleted.",
                    "Are you sure you want to leave this count?",
                ),
                margin_bottom="1rem",
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
                rx.button(
                    "Leave",
                    on_click=CountState.confirm_leave,
                    color_scheme="red",
                ),
                justify="end",
                spacing="3",
                class_name="w-full",
            ),
            max_width="26rem",
        ),
        open=CountState.leave_open,
        on_open_change=CountState.set_leave_open,
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
            _leave_dialog(),
            spacing="5",
        ),
    )
