from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.person_model import PersonModel


class MarriageModel(Base):
    __tablename__ = "marriages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    husband_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )

    wife_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, index=True
    )

    married_at: Mapped[date] = mapped_column(Date, nullable=False)

    divorced_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    husband: Mapped[PersonModel] = relationship(
        "PersonModel", foreign_keys=[husband_id], lazy="joined"
    )

    wife: Mapped[PersonModel] = relationship(
        "PersonModel", foreign_keys=[wife_id], lazy="joined"
    )

    __table_args__ = (
        UniqueConstraint(
            "husband_id", "wife_id", "married_at", name="uq_marriage_couple_date"
        ),
        CheckConstraint("husband_id != wife_id", name="ck_marriage_no_self_marriage"),
        Index("ix_marriage_husband_wife", "husband_id", "wife_id"),
    )
