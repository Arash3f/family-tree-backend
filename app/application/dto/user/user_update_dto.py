from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType


class UserUpdateField(StrEnum):
    USERNAME = "username"
    FULLNAME = "fullname"
    PASSWORD = "password"  # pragma: allowlist secret # nosec B105
    RE_PASSWORD = "re_password"  # pragma: allowlist secret # nosec B105
    EMAIL = "email"
    PHONE = "phone"
    COUNTRY_CODE = "country_code"
    ROLE_ID = "role_id"
    ACCOUNT_TYPE = "account_type"


class _UserUpdateDataDTO(BaseModel):
    username: str | None = None
    fullname: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)
    re_password: str | None = Field(default=None, min_length=8, max_length=256)
    email: str | None = None
    phone: str | None = None
    country_code: str | None = None
    role_id: UUID | None = None
    account_type: AccountType | None = None


class _UserUpdateWhereDTO(BaseModel):
    user_id: UUID


class UserUpdateDTO(BaseModel):
    data: _UserUpdateDataDTO
    where: _UserUpdateWhereDTO


class UserUpdateResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    email: str | None = None
    phone: str | None = None
    role_id: UUID | None
    account_type: AccountType
    is_active: bool = True


class UserUpdateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserUpdateResponseDTO:
        return UserUpdateResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
            account_type=user.account_type,
            is_active=user.is_active,
        )
