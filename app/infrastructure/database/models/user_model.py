from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .role_model import RoleModel


class UserModel(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )

    # -------------------------
    # relationships
    # -------------------------

    role: Mapped["RoleModel | None"] = relationship(  # type: ignore
        "RoleModel",
        foreign_keys=[role_id],
        back_populates="users",
    )
