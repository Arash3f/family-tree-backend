from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .person_model import PersonModel


class MarriageModel(Base):
    __tablename__ = "marriages"

    husband_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )

    wife_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )

    married_at: Mapped[date] = mapped_column(Date, nullable=False)

    divorced_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # -------------------------
    # relationships
    # -------------------------

    husband: Mapped["PersonModel"] = relationship(
        "PersonModel", foreign_keys=[husband_id], lazy="joined"
    )

    wife: Mapped["PersonModel"] = relationship(
        "PersonModel", foreign_keys=[wife_id], lazy="joined"
    )

    __table_args__ = (
        UniqueConstraint(
            "husband_id", "wife_id", "married_at", name="uq_marriage_couple_date"
        ),
        CheckConstraint("husband_id != wife_id", name="ck_marriage_no_self_marriage"),
        Index("ix_marriage_husband_wife", "husband_id", "wife_id"),
    )
