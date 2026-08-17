from uuid import UUID

from pydantic import BaseModel

from app.domain.shared.account_type import AccountType


class _Permission(BaseModel):
    id: UUID
    name: str
    description_en: str = ""
    description_fa: str = ""


class _RoleData(BaseModel):
    id: UUID
    name: str
    permissions: list[_Permission]


class UserGetWithDetailResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None
    account_type: AccountType
    role: _RoleData | None
