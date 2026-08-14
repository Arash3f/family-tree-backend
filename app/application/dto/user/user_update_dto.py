from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User


class UserUpdateField(str, Enum):
    USERNAME = "username"
    FULLNAME = "fullname"
    PASSWORD = "password"  # pragma: allowlist secret # nosec B105
    RE_PASSWORD = "re_password"  # pragma: allowlist secret # nosec B105
    ROLE_ID = "role_id"


class _UserUpdateDataDTO(BaseModel):
    username: str | None = None
    fullname: str | None = None
    password: str | None = None
    re_password: str | None = None
    role_id: UUID | None = None


class _UserUpdateWhereDTO(BaseModel):
    user_id: UUID


class UserUpdateDTO(BaseModel):
    data: _UserUpdateDataDTO
    where: _UserUpdateWhereDTO


class UserUpdateResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None


class UserUpdateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserUpdateResponseDTO:
        return UserUpdateResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            role_id=user.role_id,
        )
