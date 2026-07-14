"""Data-access helpers for the ``Count`` table."""

import enum
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from hachicount.db.models import Count, Participant
from hachicount.db.participants import count_participants, remove_participant


class LeaveOutcome(enum.Enum):
    """What happened when a user left a count."""

    LEFT = enum.auto()  # the user left; the count still has other participants
    DELETED = enum.auto()  # the user was the last participant; the count is gone
    NOT_A_MEMBER = enum.auto()  # the count no longer exists (nothing to leave)


def create_count(session: Session, *, name: str) -> Count:
    """Insert a new count and return it (with its generated id)."""
    count = Count(id=uuid4(), name=name)
    session.add(count)
    session.flush()  # emit the INSERT so the id is queryable within the tx
    return count


def delete_count(session: Session, count_id: UUID) -> None:
    """Delete the count with this id (a no-op if it does not exist)."""
    session.execute(delete(Count).where(Count.id == count_id))
    session.flush()


def leave_count(session: Session, *, count_id: UUID, user_id: UUID) -> LeaveOutcome:
    """Remove a user from a count, deleting the count if it becomes empty.

    Takes a row lock on the count (``SELECT ... FOR UPDATE``) for the whole
    transaction, so concurrent leaves on the *same* count serialise instead of
    interleaving. That guarantees the genuinely last leaver observes zero
    remaining participants and deletes the count — it can never be orphaned with
    no participants, regardless of what any client's cached state believed.
    """
    count = session.scalars(
        select(Count).where(Count.id == count_id).with_for_update()
    ).one_or_none()
    if count is None:
        return LeaveOutcome.NOT_A_MEMBER

    remove_participant(session, count_id=count_id, user_id=user_id)
    if count_participants(session, count_id) == 0:
        delete_count(session, count_id)
        return LeaveOutcome.DELETED
    return LeaveOutcome.LEFT


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
