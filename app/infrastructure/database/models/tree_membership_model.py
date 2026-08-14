from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.family_tree_model import FamilyTreeModel
    from app.infrastructure.database.models.user_model import UserModel


class TreeMembershipModel(Base):
    __tablename__ = "tree_memberships"

    tree_id: Mapped[UUID] = mapped_column(
        ForeignKey("family_trees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    permissions: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["view"],
        server_default='["view"]',
    )

    __table_args__ = (
        UniqueConstraint("tree_id", "user_id", name="uq_tree_membership_tree_user"),
        CheckConstraint(
            "role IN ('owner', 'member')",
            name="ck_tree_membership_role",
        ),
    )

    tree: Mapped["FamilyTreeModel"] = relationship(
        "FamilyTreeModel",
        back_populates="memberships",
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[user_id],
    )
