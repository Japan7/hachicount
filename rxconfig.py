import dotenv
import reflex as rx

# Load OIDC_CLIENT_ID / OIDC_CLIENT_SECRET / OIDC_ISSUER_URI (and friends) from a
# local .env file. Reflex only auto-loads dotenv files listed in REFLEX_ENV_FILE,
# so we load it here explicitly to keep local setup a single-file affair.
dotenv.load_dotenv()

config = rx.Config(
    app_name="hachicount",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
