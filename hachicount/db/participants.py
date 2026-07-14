"""Data-access helpers for the ``Participant`` table."""

from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from hachicount.db.models import Participant, User


def add_participant(
    session: Session, *, count_id: UUID, user: User, name: str
) -> Participant:
    """Add ``user`` to the given count as a participant displayed as ``name``."""
    participant = Participant(
        id=uuid4(), name=name, count_id=count_id, user_id=user.id
    )
    session.add(participant)
    session.flush()  # emit the INSERT so the id is queryable within the tx
    return participant


def count_participants(session: Session, count_id: UUID) -> int:
    """Return how many participants the given count has."""
    total = session.scalar(
        select(func.count()).select_from(Participant).where(
            Participant.count_id == count_id
        )
    )
    return total or 0


def remove_participant(session: Session, *, count_id: UUID, user_id: UUID) -> None:
    """Remove ``user_id``'s participation in the given count (a no-op if absent)."""
    session.execute(
        delete(Participant).where(
            Participant.count_id == count_id, Participant.user_id == user_id
        )
    )
    session.flush()
