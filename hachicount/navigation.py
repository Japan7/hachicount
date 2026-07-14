"""Navigation helpers."""

import reflex as rx


def hard_redirect(url: str) -> rx.event.EventSpec:
    """Force a full-page, same-tab navigation to ``url``.

    ``rx.redirect`` client-side (react-router) navigates for same-origin URLs, so
    it never reaches a backend HTTP route in a single-port deployment (where the
    backend shares the frontend's origin), and ``is_external=True`` opens a new
    tab. This forces a real browser navigation via ``window.location.assign`` —
    what we need to reach the backend ``/auth/*`` routes in the same tab.
    """
    return rx.call_script(f"window.location.assign({url!r})")
