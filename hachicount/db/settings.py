"""Database connection settings, resolved once from the environment.

The whole connection can be overridden with ``DATABASE_URL``. Otherwise it is
built from the ``docker-compose.yml`` defaults (user/password/database all
``hachicount`` on ``localhost``), with the published port taken from ``DB_PORT``
so it stays in sync with the compose file.
"""

import os

# psycopg (v3) is the installed driver; SQLAlchemy selects it via this prefix.
_DRIVER = "postgresql+psycopg"
_DEFAULT_PORT = "5432"


def database_url() -> str:
    """The SQLAlchemy URL for the application database."""
    override = os.environ.get("DATABASE_URL")
    if override:
        return override
    port = os.environ.get("DB_PORT", _DEFAULT_PORT)
    return f"{_DRIVER}://hachicount:hachicount@localhost:{port}/hachicount"
