from enum import Enum
from typing import List

from pydantic import BaseModel

from app.domain.entities.role import Role


class RoleUpdateField(str, Enum):
    NAME = "name"
    PERMISSION_IDS = "permission_ids"


class _RoleUpdateDataDTO(BaseModel):
    name: str | None
    permission_ids: List[int] | None


class _RoleUpdateWhereDTO(BaseModel):
    role_id: int


class RoleUpdateDTO(BaseModel):
    data: _RoleUpdateDataDTO
    where: _RoleUpdateWhereDTO


class RoleUpdateResponseDTO(BaseModel):
    id: int
    name: str


class RoleUpdateMapper(BaseModel):
    @staticmethod
    def to_response(role: Role) -> RoleUpdateResponseDTO:
        assert role.id is not None

        return RoleUpdateResponseDTO(
            id=role.id,
            name=role.name,
        )
