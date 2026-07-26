from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.role import Role


class RoleCreateDTO(BaseModel):
    name: str
    permission_ids: List[UUID]


class RoleCreateResponseDTO(BaseModel):
    id: UUID
    name: str
    permission_ids: List[UUID]


class RoleCreateMapper(BaseModel):
    @staticmethod
    def to_response(role: Role) -> RoleCreateResponseDTO:
        return RoleCreateResponseDTO(
            id=role.safe_id, name=role.name, permission_ids=role.permission_ids
        )
