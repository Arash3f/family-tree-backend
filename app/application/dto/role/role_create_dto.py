from typing import List

from pydantic import BaseModel

from app.domain.entities.role import Role


class RoleCreateDTO(BaseModel):
    name: str
    permission_ids: List[int]


class RoleCreateResponseDTO(BaseModel):
    id: int
    name: str
    permission_ids: List[int]


class RoleCreateMapper(BaseModel):
    @staticmethod
    def to_response(role: Role) -> RoleCreateResponseDTO:
        return RoleCreateResponseDTO(
            id=role.safe_id, name=role.name, permission_ids=role.permission_ids
        )
