from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.tree_membership_model import (
        TreeMembershipModel,
    )
    from app.infrastructure.database.models.user_model import UserModel


class FamilyTreeModel(Base):
    __tablename__ = "family_trees"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[owner_user_id],
    )

    memberships: Mapped[list["TreeMembershipModel"]] = relationship(
        "TreeMembershipModel",
        back_populates="tree",
        cascade="all, delete-orphan",
    )
