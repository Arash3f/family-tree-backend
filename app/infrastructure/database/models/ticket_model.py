from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.enums.ticket_status import TicketStatus
from app.infrastructure.database.base import Base

_TICKET_STATUSES = ", ".join(f"'{status.value}'" for status in TicketStatus)

if TYPE_CHECKING:
    from .ticket_message_model import TicketMessageModel
    from .user_model import UserModel


class TicketModel(Base):
    __tablename__ = "tickets"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(f"status IN ({_TICKET_STATUSES})", name="ck_ticket_status"),
    )

    created_by: Mapped["UserModel"] = relationship(  # type: ignore
        "UserModel",
        foreign_keys=[created_by_user_id],
    )

    messages: Mapped[List["TicketMessageModel"]] = relationship(  # type: ignore
        "TicketMessageModel",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessageModel.created_at",
    )
