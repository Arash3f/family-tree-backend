from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType


class UserCreateDTO(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=255,
        description="Username must be 3-255 characters",
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    fullname: str = Field(
        min_length=1,
        max_length=500,
        description="Full name must be 1-500 characters",
    )
    password: str = Field(
        min_length=8,
        max_length=256,
        description="Password must be 8-256 characters",
    )
    re_password: str = Field(
        min_length=8,
        max_length=256,
        description="Password must be 8-256 characters",
    )
    role_id: UUID | None
    account_type: AccountType = AccountType.FREE


class UserCreateResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType


class UserCreateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserCreateResponseDTO:
        return UserCreateResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            role_id=user.role_id,
            account_type=user.account_type,
        )
