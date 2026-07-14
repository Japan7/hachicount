"""Data-access helpers for the ``User`` table."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from hachicount.db.errors import UserNotFoundError
from hachicount.db.models import User


def get_user_by_email(session: Session, email: str) -> User | None:
    """Return the user with this email, or ``None`` if there is none."""
    return session.scalars(select(User).where(User.email == email)).one_or_none()


def get_or_create_user(session: Session, *, email: str, name: str) -> User:
    """Return the user for ``email``, creating one seeded with ``name`` if absent.

    Idempotent: an existing account is returned untouched, so ``name`` only ever
    seeds a brand-new row — it is the user's to edit afterwards and is never
    overwritten here.
    """
    user = get_user_by_email(session, email)
    if user is None:
        user = User(id=uuid4(), name=name, email=email)
        session.add(user)
        session.flush()  # emit the INSERT so the row is queryable within the tx
    return user


def update_user_name(session: Session, *, email: str, name: str) -> User:
    """Rename the user with this email.

    Raises :class:`UserNotFoundError` when no such user exists, rather than
    silently doing nothing.
    """
    user = get_user_by_email(session, email)
    if user is None:
        raise UserNotFoundError(email)
    user.name = name
    return user


def get_or_create_user_from_claims(session: Session, claims: dict[str, Any]) -> User:
    """Provision (or fetch) the local account for a set of verified id_token claims.

    Our provider sets the ``sub`` claim to the user's email, so that is the
    stable account identity. ``name``/``preferred_username`` (falling back to the
    email local-part) seed a display name for brand-new accounts only.
    """
    email = claims["sub"]
    name = claims.get("name") or claims.get("preferred_username") or email.split("@")[0]
    return get_or_create_user(session, email=email, name=name)
