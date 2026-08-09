from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.marriage_model import MarriageModel
    from app.infrastructure.database.models.parent_link_model import ParentLinkModel


class PersonModel(Base):
    __tablename__ = "persons"

    name: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    marriage_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("marriages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    photo_object_key: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "name",
            "marriage_id",
            name="uq_person_name_marriage",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date",
            name="ck_person_death_after_birth",
        ),
        CheckConstraint(
            "gender IN ('male', 'female')",
            name="ck_person_gender",
        ),
    )

    # -------------------------
    # relationships
    # -------------------------

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
