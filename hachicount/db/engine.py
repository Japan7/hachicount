"""The SQLAlchemy engine, session factory, and unit-of-work helper.

Owns the single process-wide engine and hands out short-lived sessions through
``transaction()``, a context manager that commits on success and rolls back on
any error. ``create_tables()`` issues the DDL for the declared models — a
stand-in until a real migration tool is introduced.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from hachicount.db.models import Base
from hachicount.db.settings import database_url

engine = create_engine(database_url())

# ``expire_on_commit=False`` keeps loaded instances usable after the commit, so
# callers can still read a freshly persisted row's fields once the block exits.
_new_session = sessionmaker(engine, expire_on_commit=False)


@contextmanager
def transaction() -> Iterator[Session]:
    """A database session scoped to a single unit of work.

    Commits when the block exits cleanly, rolls back on any exception, and
    always closes the session.
    """
    session = _new_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_update_tables() -> None:
    """Create any missing tables for the declared models (no migrations yet)."""
    Base.metadata.create_all(engine)
