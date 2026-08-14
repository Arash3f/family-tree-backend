from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .role_model import RoleModel


class PermissionModel(Base):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description_en: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    description_fa: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # -------------------------
    # relationships
    # -------------------------

    roles: Mapped[list["RoleModel"]] = relationship(  # type: ignore
        "RoleModel",
        secondary="role_permissions",
        back_populates="permissions",
    )
