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
        assert role.id is not None

        return RoleCreateResponseDTO(
            id=role.id, name=role.name, permission_ids=role.permission_ids
        )
