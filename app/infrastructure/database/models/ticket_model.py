from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.shared.enums.ticket_category import TicketCategory
from app.domain.shared.enums.ticket_status import TicketStatus
from app.infrastructure.database.base import Base

_TICKET_STATUSES = ", ".join(f"'{status.value}'" for status in TicketStatus)
_TICKET_CATEGORIES = ", ".join(f"'{category.value}'" for category in TicketCategory)

if TYPE_CHECKING:
    from .family_tree_model import FamilyTreeModel
    from .ticket_message_model import TicketMessageModel
    from .user_model import UserModel


class TicketModel(Base):
    __tablename__ = "tickets"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    family_tree_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("family_trees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(f"status IN ({_TICKET_STATUSES})", name="ck_ticket_status"),
        CheckConstraint(
            f"category IN ({_TICKET_CATEGORIES})", name="ck_ticket_category"
        ),
    )

    created_by: Mapped["UserModel"] = relationship(  # type: ignore
        "UserModel",
        foreign_keys=[created_by_user_id],
    )

    family_tree: Mapped["FamilyTreeModel | None"] = relationship(  # type: ignore
        "FamilyTreeModel",
        foreign_keys=[family_tree_id],
    )

    messages: Mapped[list["TicketMessageModel"]] = relationship(  # type: ignore
        "TicketMessageModel",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessageModel.created_at",
    )
