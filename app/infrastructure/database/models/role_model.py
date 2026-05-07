from typing import TYPE_CHECKING, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


if TYPE_CHECKING:
    from .permission_model import PermissionModel
    from .user_model import UserModel


class RoleModel(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # -------------------------
    # relationships
    # -------------------------

    permissions: Mapped[List["PermissionModel"]] = relationship(  # type: ignore
        "PermissionModel",
        secondary="role_permissions",
        back_populates="roles",
        lazy="joined",
    )

    users: Mapped[List["UserModel"]] = relationship(  # type: ignore
        "UserModel", back_populates="role"
    )
