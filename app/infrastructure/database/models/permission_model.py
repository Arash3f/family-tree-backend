from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from .role_model import RoleModel


class PermissionModel(Base):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # -------------------------
    # relationships
    # -------------------------

    roles: Mapped[List["RoleModel"]] = relationship(  # type: ignore
        "RoleModel",
        secondary="role_permissions",
        back_populates="permissions",
    )
