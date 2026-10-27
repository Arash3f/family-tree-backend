from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User
from app.domain.shared.account_type import AccountType


class UserGetResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    email: str | None = None
    phone: str | None = None
    role_id: UUID | None
    account_type: AccountType
    paid_until: date | None = None
    is_active: bool = True


class UserGetMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserGetResponseDTO:
        return UserGetResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
            account_type=user.account_type,
            paid_until=user.paid_until,
            is_active=user.is_active,
        )
