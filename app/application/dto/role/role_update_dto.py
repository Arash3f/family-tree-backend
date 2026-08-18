from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.role import Role


class RoleUpdateField(StrEnum):
    NAME = "name"
    PERMISSION_IDS = "permission_ids"


class _RoleUpdateDataDTO(BaseModel):
    name: str | None = None
    permission_ids: list[UUID] | None = None


class _RoleUpdateWhereDTO(BaseModel):
    role_id: UUID


class RoleUpdateDTO(BaseModel):
    data: _RoleUpdateDataDTO
    where: _RoleUpdateWhereDTO


class RoleUpdateResponseDTO(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID]


class RoleUpdateMapper(BaseModel):
    @staticmethod
    def to_response(role: Role) -> RoleUpdateResponseDTO:
        return RoleUpdateResponseDTO(
            id=role.safe_id,
            name=role.name,
            permission_ids=role.permission_ids,
        )
