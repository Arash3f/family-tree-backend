from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class PersonModel(Base):
    __tablename__ = "persons"

    name: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    father_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    mother_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "name", "father_id", "mother_id", name="uq_person_name_parents"
        ),
    )

    # -------------------------
    # relationships
    # -------------------------

    father: Mapped["PersonModel | None"] = relationship(
        "PersonModel",
        foreign_keys=[father_id],
        remote_side="PersonModel.id",
        back_populates="children_from_father",
    )

    mother: Mapped["PersonModel | None"] = relationship(
        "PersonModel",
        foreign_keys=[mother_id],
        remote_side="PersonModel.id",
        back_populates="children_from_mother",
    )

    children_from_father: Mapped[list["PersonModel"]] = relationship(
        "PersonModel",
        foreign_keys=[father_id],
        back_populates="father",
        cascade="all, delete-orphan",
    )

    children_from_mother: Mapped[list["PersonModel"]] = relationship(
        "PersonModel",
        foreign_keys=[mother_id],
        back_populates="mother",
        cascade="all, delete-orphan",
    )
