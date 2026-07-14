"""Data-access helpers for the ``Participant`` table."""

from uuid import UUID, uuid4

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
