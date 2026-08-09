from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.person_model import PersonModel


class ParentLinkModel(Base):
    __tablename__ = "parent_links"

    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("child_id", "parent_id", name="uq_parent_link_child_parent"),
        CheckConstraint("child_id != parent_id", name="ck_parent_link_no_self"),
        CheckConstraint(
            "relationship_type IN ('biological', 'adoptive', 'step')",
            name="ck_parent_link_relationship_type",
        ),
    )

    child: Mapped["PersonModel"] = relationship(
        "PersonModel",
        foreign_keys=[child_id],
        back_populates="parent_links",
    )

    parent: Mapped["PersonModel"] = relationship(
        "PersonModel",
        foreign_keys=[parent_id],
    )
