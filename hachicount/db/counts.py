"""Data-access helpers for the ``Count`` table."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from hachicount.db.models import Count, Participant


def create_count(session: Session, *, name: str) -> Count:
    """Insert a new count and return it (with its generated id)."""
    count = Count(id=uuid4(), name=name)
    session.add(count)
    session.flush()  # emit the INSERT so the id is queryable within the tx
    return count


def get_counts_for_user(session: Session, user_id: UUID) -> list[Count]:
    """Return the counts this user takes part in, ordered by name.

    A user is linked to a count through a :class:`Participant` row, so this
    joins participants to their counts and keeps only those claimed by the user.
    """
    return list(
        session.scalars(
            select(Count)
            .join(Participant, Participant.count_id == Count.id)
            .where(Participant.user_id == user_id)
            .order_by(Count.name)
            .distinct()
        ).all()
    )
