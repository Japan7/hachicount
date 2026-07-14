from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    email: Mapped[str] = mapped_column(Text(), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, email={self.email!r})"


class Count(Base):
    __tablename__ = "count"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)

    def __repr__(self) -> str:
        return f"Count(id={self.id!r}, name={self.name!r})"


class Participant(Base):
    __tablename__ = "participant"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text(), nullable=False)

    # A participant always belongs to a count. It may also be tied to a
    # registered user (``user_id``/``user`` are null for a placeholder
    # participant that nobody has claimed yet).
    count_id: Mapped[UUID] = mapped_column(ForeignKey("count.id"), nullable=False)
    count: Mapped[Count] = relationship()

    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user.id"), nullable=True
    )
    user: Mapped[Optional[User]] = relationship()

    def __repr__(self) -> str:
        return f"Participant(id={self.id!r}, name={self.name!r}, count_id={self.count_id!r})"
