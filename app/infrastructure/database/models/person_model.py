from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.family_tree_model import FamilyTreeModel
    from app.infrastructure.database.models.marriage_model import MarriageModel
    from app.infrastructure.database.models.parent_link_model import ParentLinkModel


class PersonModel(Base):
    __tablename__ = "persons"

    name: Mapped[str] = mapped_column(String, nullable=False)
    family_name: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String, nullable=True)
    death_place: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    tree_id: Mapped[UUID] = mapped_column(
        ForeignKey("family_trees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marriage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("marriages.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        index=True,
    )
    photo_object_key: Mapped[str | None] = mapped_column(String, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        Index(
            "uq_person_tree_name_marriage",
            "tree_id",
            "name",
            "marriage_id",
            unique=True,
            postgresql_where=text("marriage_id IS NOT NULL AND deleted_at IS NULL"),
        ),
        CheckConstraint(
            "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
            name="ck_person_death_after_birth",
        ),
        CheckConstraint(
            "gender IN ('male', 'female')",
            name="ck_person_gender",
        ),
        # Every person query filters out soft-deleted rows.
        Index(
            "ix_persons_active_not_deleted",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    family_tree: Mapped["FamilyTreeModel"] = relationship(
        "FamilyTreeModel",
        foreign_keys=[tree_id],
    )

    origin_marriage: Mapped["MarriageModel | None"] = relationship(
        "MarriageModel",
        foreign_keys=[marriage_id],
    )

    parent_links: Mapped[list["ParentLinkModel"]] = relationship(
        "ParentLinkModel",
        foreign_keys="ParentLinkModel.child_id",
        back_populates="child",
        cascade="all, delete-orphan",
    )
