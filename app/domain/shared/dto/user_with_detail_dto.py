from uuid import UUID

from pydantic import BaseModel


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
    role: _RoleData | None
