from typing import List
from uuid import UUID

from pydantic import BaseModel


class _Permission(BaseModel):
    id: UUID
    name: str


class _RoleData(BaseModel):
    id: UUID
    name: str
    permissions: List[_Permission]


class UserGetWithDetailResponseDTO(BaseModel):
    id: UUID
    username: str
    role_id: UUID | None
    role: _RoleData | None
