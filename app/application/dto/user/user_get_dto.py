from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType


class UserGetResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType


class UserGetMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserGetResponseDTO:
        return UserGetResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            role_id=user.role_id,
            account_type=user.account_type,
        )
