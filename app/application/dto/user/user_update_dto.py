from enum import Enum

from pydantic import BaseModel

from app.domain.entities.user import User


class UserUpdateField(str, Enum):
    USERNAME = "username"
    PASSWORD = "password"  # pragma: allowlist secret # nosec B105
    RE_PASSWORD = "re_password"  # pragma: allowlist secret # nosec B105
    ROLE_ID = "role_id"


class _UserUpdateDataDTO(BaseModel):
    username: str | None
    password: str | None
    re_password: str | None
    role_id: int | None


class _UserUpdateWhereDTO(BaseModel):
    user_id: int


class UserUpdateDTO(BaseModel):
    data: _UserUpdateDataDTO
    where: _UserUpdateWhereDTO


class UserUpdateResponseDTO(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserUpdateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserUpdateResponseDTO:
        return UserUpdateResponseDTO(
            id=user.safe_id,
            username=user.username,
            role_id=user.role_id,
        )
