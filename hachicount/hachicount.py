"""hachicount — a shared-expense tracker, behind an OIDC login wall.

This module is the composition root: it builds the app, mounts the backend auth
routes, and registers the pages. Page components live in ``hachicount.pages``,
the Reflex session guard in ``hachicount.states``, and the OIDC HTTP routes in
``hachicount.auth_api``.
"""

import reflex as rx

from hachicount.auth_api import build_auth_api
from hachicount.db.engine import create_update_tables
from hachicount.pages.index import index
from hachicount.pages.login import login
from hachicount.pages.profile import profile
from hachicount.routes import LOGIN_ROUTE, HOME_ROUTE, PROFILE_ROUTE
from hachicount.states.auth import AuthState
from hachicount.states.count import CountState
from hachicount.states.user import UserState

# `api_transformer` mounts our /api/auth/* HTTP routes alongside the Reflex app, so
# the OIDC flow can set an HttpOnly session cookie from a real HTTP response.
app = rx.App(api_transformer=build_auth_api())

# Ensure the schema exists when the server starts (a stand-in until migrations).
app.register_lifespan_task(create_update_tables)

app.add_page(
    index, route=HOME_ROUTE, on_load=[UserState.load_user, CountState.load_counts]
)
app.add_page(login, route=LOGIN_ROUTE, on_load=AuthState.redirect_if_authenticated)
app.add_page(profile, route=PROFILE_ROUTE, on_load=UserState.load_user)
