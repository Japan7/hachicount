"""hachicount — a shared-expense tracker, behind an OIDC login wall.

This module is the composition root: it builds the app, mounts the backend auth
routes, and registers the pages. Page components live in ``hachicount.pages``,
the Reflex session guard in ``hachicount.states``, and the OIDC HTTP routes in
``hachicount.auth_api``.
"""

import reflex as rx

from hachicount.auth_api import build_auth_api
from hachicount.pages.index import index
from hachicount.pages.login import login
from hachicount.routes import LOGIN_ROUTE, HOME_ROUTE
from hachicount.states.auth import AuthState

# `api_transformer` mounts our /api/auth/* HTTP routes alongside the Reflex app, so
# the OIDC flow can set an HttpOnly session cookie from a real HTTP response.
app = rx.App(api_transformer=build_auth_api())
app.add_page(index, route=HOME_ROUTE, on_load=AuthState.require_login)
app.add_page(login, route=LOGIN_ROUTE, on_load=AuthState.redirect_if_authenticated)
