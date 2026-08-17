from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType


class UserCreateDTO(BaseModel):
    username: str
    fullname: str
    password: str
    re_password: str
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
