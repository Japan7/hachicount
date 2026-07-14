# Hachicount

Nanacount, but it's working.

A [Reflex](https://reflex.dev) app whose pages sit behind an OpenID Connect
(OIDC) login wall backed by our custom OIDC provider.

## Setup

1. Install dependencies (creates/uses `.venv`):

   ```bash
   uv sync
   ```

2. Configure the OIDC provider. Copy the template and fill in the values you
   got when registering this app with the provider:

   ```bash
   cp .env.example .env
   ```

   | Variable             | Meaning                                                                 |
   | -------------------- | ----------------------------------------------------------------------- |
   | `OIDC_ISSUER_URI`    | Base issuer URL, e.g. `https://sso.example.com` (no `/.well-known/...`). |
   | `OIDC_CLIENT_ID`     | Client id issued by the provider.                                       |
   | `OIDC_CLIENT_SECRET` | Client secret issued by the provider.                                   |

   `.env` is gitignored — never commit real secrets.

3. Register the **redirect URI** with the provider: the **backend** base URL
   plus `/auth/callback`, e.g. `http://localhost:8000/auth/callback` for local
   development.

   The backend and frontend base URLs come from Reflex's own config
   (`api_url` / `deploy_url`, overridable via `REFLEX_API_URL` /
   `REFLEX_DEPLOY_URL`). In local dev these default to `http://localhost:8000`
   (backend, where the auth routes live) and `http://localhost:3000` (frontend,
   where users land). In production set both to your real URLs — a single-port
   deployment uses one origin for both — and cookies are marked `Secure`
   automatically when the backend URL is `https`.

## Run

```bash
uv run reflex run
```

Then open the app: unauthenticated visitors are redirected to `/login`, sign in
through the OIDC provider, and land on the protected home page.

## How auth works

The OIDC Authorization Code + PKCE flow runs on the **backend** so the session
cookie can be set `HttpOnly` (invisible to JavaScript/XSS) — a Reflex websocket
event can only set cookies from JS, so the flow lives in real HTTP routes:

- `hachicount/oidc/` — a framework-agnostic OIDC client, a thin wrapper over
  [Authlib](https://authlib.org)'s OIDC client that handles discovery, JWKS,
  authorization-request building (PKCE), code exchange, and ID-token
  verification. It exposes its own exception types (`OIDCError` and subclasses),
  so the rest of the app never depends on the underlying libraries' exceptions.
- `hachicount/auth_api.py` — the backend HTTP routes `/api/auth/login`,
  `/api/auth/callback`, `/api/auth/logout` (mounted via `api_transformer`). They
  drive the flow and set/clear the `HttpOnly`, `Secure` `hc_id_token` cookie.
- `hachicount/states/auth.py` — the Reflex session guard (`AuthState`): it reads
  the incoming id_token from the request's `Cookie` header and re-verifies it; it
  never writes cookies.

The id_token is a provider-signed JWT. Its signature and claims (issuer,
audience, **expiry**) are re-verified server-side on every authorization
decision, so a tampered, forged or expired cookie is always rejected.

Protect a **page** by adding `on_load=AuthState.require_login`. Protect an
**event handler** that reads or mutates private data by starting it with
`claims = await self.verify_session()` (via `await self.get_state(AuthState)`
from another state) and bailing out when it returns `None`.
