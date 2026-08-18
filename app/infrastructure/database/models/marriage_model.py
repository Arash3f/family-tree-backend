from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .family_tree_model import FamilyTreeModel
    from .person_model import PersonModel


class MarriageModel(Base):
    __tablename__ = "marriages"

    tree_id: Mapped[UUID] = mapped_column(
        ForeignKey("family_trees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    spouse_a_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    spouse_b_id: Mapped[UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    married_at: Mapped[date] = mapped_column(Date, nullable=False)

    divorced_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    family_tree: Mapped["FamilyTreeModel"] = relationship(
        "FamilyTreeModel",
        foreign_keys=[tree_id],
    )

    spouse_a: Mapped["PersonModel"] = relationship(
        "PersonModel", foreign_keys=[spouse_a_id], lazy="joined"
    )

    spouse_b: Mapped["PersonModel"] = relationship(
        "PersonModel", foreign_keys=[spouse_b_id], lazy="joined"
    )

    __table_args__ = (
        Index(
            "uq_marriage_tree_couple_date",
            "tree_id",
            "spouse_a_id",
            "spouse_b_id",
            "married_at",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint(
            "spouse_a_id != spouse_b_id", name="ck_marriage_no_self_marriage"
        ),
        CheckConstraint(
            "divorced_at IS NULL OR divorced_at >= married_at",
            name="ck_marriage_divorce_after_married",
        ),
        Index("ix_marriage_spouses", "spouse_a_id", "spouse_b_id"),
        # "Is this person currently married?" runs before every marriage
        # create, update and person delete; one index per spouse column keeps
        # that OR-predicate off a sequential scan.
        Index(
            "ix_marriage_active_spouse_a",
            "spouse_a_id",
            postgresql_where=text("divorced_at IS NULL"),
        ),
        Index(
            "ix_marriage_active_spouse_b",
            "spouse_b_id",
            postgresql_where=text("divorced_at IS NULL"),
        ),
    )
