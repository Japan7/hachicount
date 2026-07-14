"""The user's profile page: edit your display name."""

import reflex as rx

from hachicount.components.layout import authenticated_layout
from hachicount.states.user import UserState


def _field_label(text: str) -> rx.Component:
    return rx.text(text, size="1", weight="medium", color_scheme="gray")


def profile() -> rx.Component:
    """Protected profile page where the user edits their display name.

    The email is shown read-only (it is the account identity, set by the
    provider); only the name is editable. Submitting the form calls
    ``UserState.save_name``, which persists the change and reports the result.
    """
    return authenticated_layout(
        rx.vstack(
            rx.heading("Profile", size="7"),
            rx.card(
                rx.form(
                    rx.vstack(
                        _field_label("Email"),
                        rx.input(value=UserState.email, disabled=True, width="100%"),
                        _field_label("Name"),
                        rx.input(
                            name="name",
                            value=UserState.name_draft,
                            on_change=UserState.set_name_draft,
                            placeholder="Your name",
                            required=True,
                            width="100%",
                        ),
                        rx.button("Save", type="submit", margin_top="0.5rem"),
                        spacing="2",
                        width="100%",
                    ),
                    on_submit=UserState.save_name,
                ),
                width="100%",
                max_width="24rem",
            ),
            spacing="5",
            align="center",
            width="100%",
        ),
    )
