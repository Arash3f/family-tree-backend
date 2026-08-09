from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .ticket_model import TicketModel
    from .user_model import UserModel


class TicketMessageModel(Base):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[UUID] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    body: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped["TicketModel"] = relationship(  # type: ignore
        "TicketModel",
        back_populates="messages",
        foreign_keys=[ticket_id],
    )

    author: Mapped["UserModel"] = relationship(  # type: ignore
        "UserModel",
        foreign_keys=[author_user_id],
    )
